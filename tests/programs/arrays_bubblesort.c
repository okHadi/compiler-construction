int main() {
    int a[5];
    a[0] = 5;
    a[1] = 2;
    a[2] = 4;
    a[3] = 1;
    a[4] = 3;

    int i = 0;
    while (i < 5) {
        int j = 0;
        while (j < 4 - i) {
            if (a[j] > a[j + 1]) {
                int tmp = a[j];
                a[j] = a[j + 1];
                a[j + 1] = tmp;
            }
            j = j + 1;
        }
        i = i + 1;
    }

    int k = 0;
    while (k < 5) {
        print(a[k]);
        k = k + 1;
    }
    return 0;
}
