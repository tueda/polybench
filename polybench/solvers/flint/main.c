#include <flint/fmpz_mpoly.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

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
    const char* line = readline(infile);
    if (!line) {
      break;
    }

    if (strncmp(line, "gcd", 3) == 0) {
      char* s = &line[4];
      s[strlen(s) - 1] = '\0';

      char* polys_str;
      char** polys;
      int n_polys = strsplit(s, ",", &polys_str, &polys);

      do_gcd(n_variables, variables, n_polys, polys, outfile);

      free(polys_str);
      free(polys);
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
