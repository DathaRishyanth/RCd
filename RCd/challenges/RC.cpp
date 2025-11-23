#include <iostream>
#include <sstream>   // stringstream
#include <vector>    // vector
#include <string>    // string
#include <functional> // if you switch to std::function later
#include <cmath>     // math ops (pow, abs, etc.)
using namespace std;

/////////////////////////////////////////////////////////////////////////////////////////////////////////////

class problem{
    public:
    string prompt;
    void (*prob)(string s);
    problem(string _prompt,void f(string s)){
        prompt = _prompt;
        prob = f;
    }
};

//////////////////////////////////////////////////////////////////////////////////////////////////////////////

vector<int> get_ints(string s){
    stringstream stream(s);
    int number;
    vector<int> numbers;
    while (stream >> number) {
        numbers.push_back(number); // Add each extracted integer to the vector
    }
    return numbers;
}
void fetch(stringstream &ss, string& str, int &a, int &b){
    if (!(ss >> str >> a >> b)) {
        cout << "Invalid Input" << endl;
        str = "";
        return;
    }

    string extra;// Optional: check for extra input
    if (ss >> extra) {
        cout << "Invalid Input" << endl;
        str = "";
        return;
    }
}
void fetch(stringstream &ss, string &str, int &a){
    if (!(ss >> str >> a)) {
        cout << "Invalid Input" << endl;
        str = "";
        return;
    }

    string extra;// Optional: check for extra input
    if (ss >> extra) {
        cout << "Invalid Input" << endl;
        str = "";
        return;
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////

problem p1("Enter a single integer in the range [3,50]",[](string s){
    auto num = get_ints(s);
    if(num.size()!=1 || num[0]>50 || num[0]<3){
        cout<<"Invalid Input"<<endl;
        return;
    }

    int n = num[0];
    vector<double> fib(n+1);
    fib[1]=1.414;fib[2]=1.732;

    for(int i=3;i<n+1;i++){
        fib[i] = fib[i-1]+fib[i-2];
    }
    cout<<fib[n]<<endl;

});

problem p2("Enter 3 integers 'a b c'(only space between them) such that a>0 and 1000>=|a|,|b|,|c|.",[](string s){
    vector<int> num = get_ints(s);
    if( num.size()!=3 || num[0]<1 || num[0]>1000 || num[1] >1000 || num[1] <-1000 || num[2] > 1000 || num[2] < -1000 ){
        cout<<"Invalid Input"<<endl;
        return;
    }
    cout << (-num[1]*num[1]/((double)4.0*num[0])) + num[2] << endl;

});

problem p3("Enter 2 integers 'a b'(only space between them) such that and 20 > a,b >0.",[](string s){
    vector<int> num = get_ints(s);
    if( num.size()!=2 || num[0]<1 || num[0]>=20 || num[1] >=20 || num[1] <1){
        cout<<"Invalid Input"<<endl;
        return;
    }
    int n = num[0];int r = num[1];
    n = n + r -1;
    if (r > n - r) r = n - r;

    long long int result = 1;
    for (int i = 1; i <= r; ++i) {
        result *= (n - r + i);
        result /= i;
    }
    cout<<result<<endl;

});

problem p4("Enter 2 integers 'a b'(only space between them) such that and 1e+9 > a,b >1.",[](string s){
    vector<int> num = get_ints(s);
    if( num.size()!=2 || num[0]<=1 || num[0]>=1e+9 || num[1] <=1 || num[1] >1e+9){
        cout<<"Invalid Input"<<endl;
        return;
    }
    int a=num[0], b=num[1];
    int cnt=0;
    while(a%b==0){
        a/=b;
        cnt++;
    }
    cout << cnt << endl;

});

problem p5("Enter 3 integers 'a b c'(only space between them) [1e+9 > a,b >= 0 ; 1e+9 > c >= 1].",[](string s){
    vector<int> num = get_ints(s);
    if( num.size()!=3 || num[0]<0 || num[0]>=1e+9 || num[1] <0 || num[1] >1e+9 || num[2] <1 || num[2] >1e+9){
        cout<<"Invalid Input"<<endl;
        return;
    }
    int a=num[0], b=num[1], c = num[2];
    cout<<((a%c)+(b%c))%c<<endl;

});

problem p6("Enter any number of integers with only space between (1e+9 > |a[i]|).",[](string s){
    vector<int> num = get_ints(s);
    if (num.size()==0){
        cout<<"No/Wrong Input"<<endl;
        return;
    }
    int maxval = num[0];
    int ind = 0;
    for(int i=1; i<num.size(); i++){
        int x=num[i];
        if(x>maxval){
            maxval=x;
            ind = i;
        }
    }
    cout << ind+1 <<endl;

});

problem p7("Enter any number of integers with only space between (1e+9 > |a[i]|).",[](string s){
    vector<int> num = get_ints(s);
    if (num.size()==0){
        cout<<"No/Wrong Input"<<endl;
        return;
    }

    int ans=0;
    for(int i=0; i<num.size(); i++){
        ans^=num[i];
    }
    cout << ans << endl;
});

char increment_char(char a,int m){
        if(a<='z' && a>='a'){
            int temp = (int)(a-'a');
            temp = (temp+m)%26;
            a=(char)('a'+temp);
            return a;
        }else{
            return '\0';
        } 
}

void increment_string(string &s,int m){
    for(int i=0; i<s.size(); i++){
        s[i] = increment_char(s[i],m);
        if(s[i]=='\0'){
            s = "";
            return;
        }
    }
}

problem p8("Enter a non-empty string(s) followed by two numbers(a b) 's a b'.\n(1e+9 > a,b > 0 ; s only has lower alphabets)",[](string s){
    stringstream ss(s);
    string str; int a, b;
    fetch(ss,str,a,b);
    if(str.empty()){
        return;
    }

    if(a <= 0 || b <= 0){
        cout<<"Invalid numbers"<<endl;
        return;
    }
    increment_string(str,a);
    if(str.empty()){
        cout<<"Invalid string"<<endl;
        return;
    }

    b%=str.size();
    for(int i=b; i<str.size(); i++){
        cout << str[i];
    }for(int i=0; i<b; i++){
        cout << str[i];
    }cout << endl;

});

problem p9("Enter a non-empty string(s) followed by a numbers(a) 's a'.\n(1e+9 > a > 0 ; s only has lowercase alphabets)",[](string s){
    stringstream ss(s);
    string str;int a;
    fetch(ss,str,a);
    if(str.empty()){
        return;
    }

    if(a <= 0 ){
        cout<<"Invalid number"<<endl;
        return;
    }
    str[0] = increment_char(str[0],a);
    if(str[0]=='\0'){ cout<<"Invalid string"<<endl;return;}

    for(int i=1;i<str.size();i++){
        str[i] = increment_char(str[i],str[i-1]-'a'+1);
        if(str[i]=='\0'){ cout<<"Invalid string"<<endl;return;}
    }
    cout<<str<<endl;
});

/////////////////////////////////////////////////////////////////////////////////////////////////////////////


int main() {
    problem problems[] = {p1,p2,p3,p4,p5,p6,p7,p8,p9};
    int state = 0;
    string s;
    int n_probs = sizeof(problems)/sizeof(problem);
    while(true){
        if(state == 0){
            cout << "Enter question number: (1 to " << n_probs << "): " << endl;
        }
        else{
            cout << problems[state-1].prompt << endl;
        }
        try {
            getline(cin,s);
            if (s == "-1") {
                state = 0;
                cout << "Exiting to Main Menu" << endl;
            } else if (state == 0) {
                state = stoi(s);
                cout << "Entered problem " << s << endl;
            } 
            else{
                problems[state-1].prob(s);
            }
        } catch (const exception& e) {
            cout << "EOF or invalid input" << endl;
            state = 0;
        }
    }
    return 0;
}
