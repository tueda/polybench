#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <flint/fmpz_mpoly.h>
#include <flint/fmpz_mpoly_factor.h>

#include "version.h"

void error(const char* msg) {
  fprintf(stderr, "error: %s\n", msg);
  exit(EXIT_FAILURE);
}

void* malloc2(size_t size) {
  void* p = malloc(size);
  if (!p) {
    error("failed to allocate memory");
  }
  return p;
}

void* realloc2(void* ptr, size_t new_size) {
  void* p = realloc(ptr, new_size);
  if (!p) {
    error("failed to allocate memory");
  }
  return p;
}

long long get_nanoseconds(void) {
  struct timespec ts;
  timespec_get(&ts, TIME_UTC);
  return ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

int strsplit(const char* str, const char* delim, char** out_buf,
             char*** out_array) {
  char* buf = (char*)malloc2(sizeof(char) * (strlen(str) + 1));

  strcpy(buf, str);

  int n = 0;
  char* p = strtok(buf, delim);
  for (;;) {
    if (p) {
      n++;
      p = strtok(NULL, delim);
    } else {
      break;
    }
  }

  char** array = (char**)malloc2(sizeof(char*) * (n > 0 ? n : 1));

  int i = 0;
  strcpy(buf, str);
  p = strtok(buf, delim);
  for (;;) {
    if (p) {
      array[i] = p;
      i++;
      p = strtok(NULL, delim);
    } else {
      break;
    }
  }

  *out_buf = buf;
  *out_array = array;
  return n;
}

char* readline(FILE* file) {
  int capacity = 128;
  int size = 0;
  char* line = malloc2(sizeof(char) * capacity);
  int eof = 0;
  for (;;) {
    int c = fgetc(file);
    if (c == EOF) {
      eof = 1;
      break;
    }
    if (c == '\n') {
      break;
    }
    if (size + 1 >= capacity) {
      capacity *= 2;
      line = realloc2(line, capacity);
    }
    line[size++] = c;
  }

  if (size == 0 && eof) {
    free(line);
    return NULL;
  }

  line[size] = '\0';
  return line;
}

void do_gcd(int n_variables, const char** variables, int n_polys,
            const char** polys, FILE* out) {
  if (n_polys != 2) {
    error("npolys != 2");
  }

  fmpz_mpoly_ctx_t ctx;
  fmpz_mpoly_t p1, p2, g;
  fmpz_mpoly_ctx_init(ctx, n_variables, ORD_LEX);
  fmpz_mpoly_init(p1, ctx);
  fmpz_mpoly_init(p2, ctx);
  fmpz_mpoly_init(g, ctx);

  if (fmpz_mpoly_set_str_pretty(p1, polys[0], variables, ctx)) {
    error("failed to parse a polynomial");
  }

  if (fmpz_mpoly_set_str_pretty(p2, polys[1], variables, ctx)) {
    error("failed to parse a polynomial");
  }

  long long t1 = get_nanoseconds();
  int result = fmpz_mpoly_gcd(g, p1, p2, ctx);
  long long t2 = get_nanoseconds();

  fprintf(out, "%g,", (double)(t2 - t1) * 1.0e-9);
  if (result) {
    fmpz_mpoly_fprint_pretty(out, g, variables, ctx);
  } else {
    fprintf(out, "FAILED");
  }
  fprintf(out, "\n");

  fmpz_mpoly_clear(p1, ctx);
  fmpz_mpoly_clear(p2, ctx);
  fmpz_mpoly_clear(g, ctx);
  fmpz_mpoly_ctx_clear(ctx);
}

void do_factor(int n_variables, const char** variables, int n_polys,
               const char** polys, FILE* out) {
  if (n_polys != 1) {
    error("npolys != 1");
  }

  fmpz_mpoly_ctx_t ctx;
  fmpz_mpoly_t p;
  fmpz_mpoly_factor_t f;
  fmpz_t c;

  fmpz_mpoly_ctx_init(ctx, n_variables, ORD_LEX);
  fmpz_mpoly_init(p, ctx);
  fmpz_mpoly_factor_init(f, ctx);
  fmpz_init(c);

  if (fmpz_mpoly_set_str_pretty(p, polys[0], variables, ctx)) {
    error("failed to parse a polynomial");
  }

  long long t1 = get_nanoseconds();
  int result = fmpz_mpoly_factor(f, p, ctx);
  long long t2 = get_nanoseconds();

  fprintf(out, "%g", (double)(t2 - t1) * 1.0e-9);
  if (result) {
    slong n = fmpz_mpoly_factor_length(f, ctx);
    fmpz_mpoly_factor_get_constant_fmpz(c, f, ctx);
    if (fmpz_is_one(c)) {
      if (n == 0) {
        fprintf(out, ",1");
      }
    } else {
      fprintf(out, ",");
      fmpz_fprint(out, c);
    }
    for (slong i = 0; i < n; i++) {
      fmpz_mpoly_factor_get_base(p, f, i, ctx);
      slong k = fmpz_mpoly_factor_get_exp_si(f, i, ctx);
      fprintf(out, ",(");
      fmpz_mpoly_fprint_pretty(out, p, variables, ctx);
      fprintf(out, ")^");
      flint_fprintf(out, "%wd", k);
    }
  } else {
    fprintf(out, ",FAILED");
  }
  fprintf(out, "\n");

  fmpz_mpoly_clear(p, ctx);
  fmpz_mpoly_factor_clear(f, ctx);
  fmpz_mpoly_ctx_clear(ctx);
  fmpz_clear(c);
}

void solve(void (*f)(int, const char**, int, const char**, FILE*),
           const char* s, int n_variables, const char** variables, FILE* out) {
  char* polys_str;
  char** polys;
  int n_polys = strsplit(s, ",", &polys_str, &polys);

  f(n_variables, variables, n_polys, (const char**)polys, out);

  free(polys_str);
  free(polys);
}

int main(int argc, char* argv[]) {
  if (argc == 2 && strcmp(argv[1], "-v") == 0) {
    printf("flint %s, %s\n", FLINT_VERSION, COMPILER_VERSION);
    exit(EXIT_SUCCESS);
  }

  if (argc != 4) {
    error("argc != 4");
  }

  char* variables_str;
  char** variables;
  int n_variables = strsplit(argv[1], ",", &variables_str, &variables);

  if (n_variables < 0) {
    error("n_variables < 0");
  }

  FILE* infile = fopen(argv[2], "r");

  if (!infile) {
    error("cannot open the input file");
  }

  FILE* outfile = fopen(argv[3], "w");

  if (!outfile) {
    error("cannot open the output file");
  }

  for (;;) {
    char* line = readline(infile);
    if (!line) {
      break;
    }

    char last_char = line[strlen(line) - 1];

    if (strncmp(line, "gcd(", 4) == 0 && last_char == ')') {
      char* s = &line[4];
      s[strlen(s) - 1] = '\0';
      solve(do_gcd, s, n_variables, (const char**)variables, outfile);
    } else if (strncmp(line, "factor(", 7) == 0 && last_char == ')') {
      char* s = &line[7];
      s[strlen(s) - 1] = '\0';
      solve(do_factor, s, n_variables, (const char**)variables, outfile);
    } else {
      error("unsupported problem type");
    }
    free(line);
  }

  fclose(infile);
  fclose(outfile);
  free(variables_str);
  free(variables);
}
