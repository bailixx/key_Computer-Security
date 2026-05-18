#include <stdio.h>
#include <math.h>

int main() {
    int N;
    char symbol;
    
    if (scanf("%d %c", &N, &symbol) != 2) return 0;

    int n = sqrt((N + 1) / 2);

    for (int i = n; i >= 1; i--)
    {
        for (int j = 0; j < n - i; j++)
        {
            printf(" ");
        }
        for (int j = 0; j < 2 * i - 1; j++)
        {
            printf("%c", symbol);
        }
        printf("\n");
    }

    for (int i = 2; i <= n; i++)
    {
        for (int j = 0; j < n - i; j++)
        {
            printf(" ");
        }
        for (int j = 0; j < 2 * i - 1; j++)
        {
            printf("%c", symbol);
        }
        printf("\n");
    }

    int used = 2 * n * n - 1;
    printf("%d\n", N - used);

    return 0;
}