int g = 100;

int main() {
    int x = 1;
    {
        int x = 2;
        print(x);
    }
    print(x);
    print(g);
    return 0;
}
