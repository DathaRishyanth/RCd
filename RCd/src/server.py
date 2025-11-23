import socket
import threading
import subprocess
import os
import time
import random
from RCd.src import users
from RCd.mail.mailer import send_otp, send_forgot_passwd_mail
import RCd.config as config
from RCd.src.users.User import get_passwd, add_user, authenticate, load_users, init_admin, Player, encrypt_data
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RC_PATH = os.path.join(BASE_DIR, "RC.out")


ADDR = (config.SERVER, config.PORT)
FORMAT = 'UTF-8'
HOST_ADDRESS = socket.gethostbyname(socket.gethostname())
MSG_LENGTH = 1024

# Reuse ports
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

# Add global lock
user_list_lock = threading.Lock()

# ensure log directory exists
os.makedirs("./log", exist_ok=True)

def log(logstr):
    if config.LOGS:
        with open("./log/logs.txt", "a") as f:
            f.write(logstr)

def is_valid_uname(uname):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, uname))

def make_otp():
    return random.randint(1000, 9999)

def verify_email(conn, uname):
    email = uname
    otp = make_otp()
    send_otp(email, otp)
    conn.send(f"An OTP has been sent to {email}\n")
    conn.send(f"Enter OTP: ")
    user_otp = conn.recv(MSG_LENGTH)
    if otp == int(user_otp):
        conn.send("Email verified!\n")
        return True
    else:
        return False

def pw_check(pw, username, pw_strength):
    min_pw_len = 8
    checks = [
        len(pw) >= min_pw_len,
        re.search(r"[A-Z]", pw) and re.search(r"[a-z]", pw),
        re.search(r"[0-9]", pw),
        re.search(r"[^A-Za-z0-9]", pw),
        username not in pw,
    ]
    return all(checks[:pw_strength])

def create_pw_for_user(conn, uname):
    conn.send("Enter password: ")
    passwd = conn.recv(MSG_LENGTH)
    pw_checks = pw_check(passwd, uname, config.PASSWORD_SECURTIY_LEVEL)
    if not pw_checks:
        error_msg = [
            "minimum length of 8 characters",
            "uppercase, lowercase letters",
            "digits",
            "special symbols",
            "username not in password",
        ]
        err_msg = "Make sure your password has:\n" + ", ".join(
            error_msg[: config.PASSWORD_SECURTIY_LEVEL]
        ) + "\n"
        conn.send(err_msg)
        return
    conn.send("Confirm password: ")
    cpasswd = conn.recv(MSG_LENGTH)
    if passwd != cpasswd:
        conn.send("Passwords do not match, try again!\n")
        return
    else:
        add_user(user_list, Player(uname, passwd))
        conn.send("User created!\n")

def start_auth(conn):
    global user_list
    for i in range(3):
        conn.send("Enter email ID: ")
        uname = conn.recv(MSG_LENGTH)
        uname = uname.lower()
        if not is_valid_uname(uname):
            conn.send("Invalid email, try again!\n")
            continue
        if uname not in user_list:
            conn.send(
                f"User not found, create new account with username {uname}? [Y/n]:\n"
            )
            resp = conn.recv(MSG_LENGTH)
            if resp.lower() == "y" or resp == "":
                conn.send("Creating new user...\n")
                if not config.VERIFY_MAIL or verify_email(conn, uname):
                    create_pw_for_user(conn, uname)
            else:
                conn.send("Try logging in again!\n")
                pass
        else:
            conn.send("Enter password: ")
            passwd = conn.recv(MSG_LENGTH)
            if authenticate(user_list, uname, passwd):
                conn.send("Logging in...\n")
                return [True, user_list[uname]]
            else:
                conn.send("Wrong password or username\n")
                conn.send("Forgot Password? [Y/n]: \n")
                response = conn.recv(MSG_LENGTH)
                if response in ("Y", "y", ""):
                    passwd = get_passwd(user_list, uname)
                    send_forgot_passwd_mail(uname, passwd)
                    conn.send(
                        "Mail succesfully sent, check your password and try logging in again!\n"
                    )
                else:
                    conn.send("Try again!\n")
                conn.send("Wrong password or username, try again!\n")
    return [False, None]

def handle_admin(conn):
    options = ["1. Test RC", "2. Add user", "3. Add new problem", "4. Exit"]
    for option in options:
        conn.send(option + "\n")
    conn.send("Enter choice : \n")
    choice = conn.recv(MSG_LENGTH)
    if choice == "1":
        handle_player(conn)
    elif choice == "2":
        conn.send("Enter username: ")
        uname = conn.recv(MSG_LENGTH)
        conn.send("Enter password: ")
        passwd = conn.recv(MSG_LENGTH)
        add_user(user_list, Player(uname, passwd))
        conn.send("User added!\n")
    elif choice == "3":
        pass
    elif choice == "4":
        conn.send("Exiting...\n")
        conn.close()
        return
    else:
        conn.send("Enter an integer for your choice\n")

def handle_player(conn, user):
    user.qlim = max(500, user.qlim)
    rc = subprocess.Popen(
        [RC_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    def forward_output():
        try:
            for line in rc.stdout:
                if not line:
                    break
                conn.send(line.rstrip())
        except Exception as e:
            log(f"[ERROR forward_output] {e}\n")

    threading.Thread(target=forward_output, daemon=True).start()

    try:
        conn.send("RC session started!\n")
        while user.qlim > 0:
            msg = conn.recv(MSG_LENGTH)
            if not msg:
                break
            user.qlim -= 1
            log(f"Recv: {msg}\n")
            try:
                rc.stdin.write(msg + "\n")
                rc.stdin.flush()
            except Exception as e:
                log(f"[ERROR write stdin] {e}\n")
                break
    finally:
        with user_list_lock:
            try:
                user_list[user.uname].active = False
            except Exception:
                pass
        try:
            rc.terminate()
        except Exception:
            pass
        conn.close()


def handle_simple(conn):
    rc = subprocess.Popen(
        [RC_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1   # line-buffered
    )

    def forward_output():
        try:
            for line in rc.stdout:
                if not line:
                    break
                conn.send(line.rstrip())
        except Exception as e:
            log(f"[ERROR forward_output] {e}\n")

    # start background thread to stream RC.out -> client
    threading.Thread(target=forward_output, daemon=True).start()

    try:
        conn.send("RC session started!\n")
        while True:
            msg = conn.recv(MSG_LENGTH)
            if not msg:
                break
            try:
                rc.stdin.write(msg + "\n")
                rc.stdin.flush()
            except Exception as e:
                log(f"[ERROR write stdin] {e}\n")
                break
    finally:
        try:
            rc.terminate()
        except Exception:
            pass
        conn.close()


def handle_client(conn, addr):
    if config.LOGIN:
        auth, user = start_auth(conn)
        if not auth:
            conn.send("Authentication failed, closing connection...\n")
            conn.close()
            return
        if user.__class__.__name__ == "Admin":
            log(f"[NEW CONNECTION] {addr} connected as Admin.\n")
            handle_admin(conn)
            log(f"[DISCONNECTED] {addr} (admin) disconnected.\n")
        elif user.__class__.__name__ == "Player":
            log(f"[NEW CONNECTION] {addr} connected.\n")
            handle_player(conn, user)
            log(f"[DISCONNECTED] {addr} disconnected.\n")
    else:
        log(f"[NEW CONNECTION] {addr} connected.\n")
        handle_simple(conn)
        log(f"[DISCONNECTED] {addr} disconnected.\n")

class conn_handler:
    def __init__(self, conn):
        self.conn = conn
        self.closed = False

    def send(self, msg):
        if self.closed:
            return False
        msg = msg.strip() + "\n"
        try:
            self.conn.send(msg.encode(FORMAT))
            return True
        except (BrokenPipeError, OSError) as e:
            try:
                log(f"[BROKEN PIPE] {str(e)}\n")
            except Exception:
                pass
            self.closed = True
            try:
                self.conn.close()
            except Exception:
                pass
            return False

    def recv(self, length):
        s = ""
        while True:
            try:
                data = self.conn.recv(length)
                if not data:
                    return ""
                ch = data.decode()
                if ch == "\x08":
                    s = s[:-1]
                else:
                    s += ch
            except (ConnectionResetError, OSError):
                return ""
            except Exception:
                return ""
            if s.endswith("\n"):
                break
        return s.strip()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

def start():
    global user_list
    if os.path.exists("users.pkl"):
        encrypt_data()
        user_list = load_users()
    else:
        init_admin()
        user_list = load_users()
    pid = os.getpid()
    print("PID: ", pid)
    print(f"<ip> <port> :\n{HOST_ADDRESS} {config.PORT}")
    server.listen()
    while True:
        try:
            conn_raw, addr = server.accept()
            conn = conn_handler(conn_raw)
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
        except KeyboardInterrupt:
            print("\n[SHUTTING DOWN] Server is shutting down...")
            break
        except Exception as e:
            log(f"[ERROR] Connection error: {str(e)}\n")
            continue

    server.close()
    print("[CLEANUP] Server socket closed. Exiting.")

if __name__ == "__main__":
    print("Starting server...")
    user_list = load_users()
    start()
    print("Success!")
