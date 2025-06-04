package com.github.tueda.polybench.rings;

import cc.redberry.rings.bigint.BigInteger;
import cc.redberry.rings.poly.PolynomialFactorDecomposition;
import cc.redberry.rings.poly.multivar.MultivariateFactorization;
import cc.redberry.rings.poly.multivar.MultivariateGCD;
import cc.redberry.rings.poly.multivar.MultivariatePolynomial;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/** Main application class. */
@SuppressWarnings("PMD.UseUtilityClass")
public class App {
  /** Entry point. */
  public static void main(final String[] args) throws IOException {
    String[] variables = args[0].split(",");
    final Path inputFile = Paths.get(args[1]);
    final Path outputFile = Paths.get(args[2]);

    try (BufferedReader in = Files.newBufferedReader(inputFile);
        PrintWriter out = new PrintWriter(Files.newBufferedWriter(outputFile))) {
      while (true) {
        final String line = in.readLine();
        if (line == null) {
          break;
        }
        String answer;
        if (line.startsWith("gcd")) {
          answer = doGcd(line, variables);
        } else if (line.startsWith("factor")) {
          answer = doFactor(line, variables);
        } else {
          String problemType = line.length() > 8 ? line.substring(0, 8) + "..." : line;
          throw new IllegalArgumentException("unknown problem type: " + problemType);
        }
        out.println(answer);
      }
    }
  }

  private static String doGcd(final String line, final String... variables) {
    String s = line.substring(4, line.length() - 1); // "gcd(p1,p2)"
    String[] input = s.split(",");
    MultivariatePolynomial<BigInteger> p1 = MultivariatePolynomial.parse(input[0], variables);
    MultivariatePolynomial<BigInteger> p2 = MultivariatePolynomial.parse(input[1], variables);
    long t1 = System.nanoTime();
    MultivariatePolynomial<BigInteger> gcd = MultivariateGCD.PolynomialGCD(p1, p2);
    long t2 = System.nanoTime();
    return (t2 - t1) / 1.0e9 + "," + gcd.toString(variables);
  }

  private static String doFactor(final String line, final String... variables) {
    String s = line.substring(7, line.length() - 1); // "factor(p)
    MultivariatePolynomial<BigInteger> p = MultivariatePolynomial.parse(s, variables);
    long t1 = System.nanoTime();
    PolynomialFactorDecomposition<MultivariatePolynomial<BigInteger>> factors =
        MultivariateFactorization.Factor(p);
    long t2 = System.nanoTime();
    StringBuilder result = new StringBuilder();
    result.append((t2 - t1) / 1.0e9 + "," + factors.unit);
    for (int i = 0; i < factors.size(); i++) {
      result.append(",(" + factors.get(i).toString(variables) + ")^" + factors.getExponent(i));
    }
    return result.toString();
  }
}
