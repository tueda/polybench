use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader, LineWriter, Write};
use std::sync::Arc;
use std::time::Instant;
use symbolica::domains::integer::Z;
use symbolica::poly::factor::Factorize;
use symbolica::poly::polynomial::MultivariatePolynomial;
use symbolica::poly::Variable;
use symbolica::{atom::AtomCore, parse, symbol};

fn main() {
    let args: Vec<_> = env::args().collect();

    let variables: Vec<_> = args[1].split(',').collect();
    let input_filename = &args[2];
    let output_filename = &args[3];

    let input_file = File::open(input_filename).unwrap();
    let output_file = File::create(output_filename).unwrap();

    let mut output = LineWriter::new(output_file);

    let var_map: Arc<Vec<Variable>> =
        Arc::new(variables.iter().map(|x| symbol!(x).into()).collect());

    for line in BufReader::new(input_file).lines() {
        let line = line.unwrap();

        if line.starts_with("gcd") {
            // The format is "gcd(poly1,poly2)". Extract poly1 and poly2.
            let line = &line[4..line.len() - 1];
            let poly_strs: Vec<_> = line.split(',').collect();
            let poly1 = get_poly(poly_strs[0], &var_map);
            let poly2 = get_poly(poly_strs[1], &var_map);

            // Compute the GCD.
            let instant = Instant::now();
            let gcd = poly1.gcd(&poly2);
            let elapsed = instant.elapsed();

            // Write the elapsed time and result.
            writeln!(
                &mut output,
                "{}.{:06},{}",
                elapsed.as_secs(),
                elapsed.subsec_micros(),
                gcd
            )
            .unwrap();
        } else if line.starts_with("factor") {
            // The format is "factor(poly)". Extract poly.
            let line = &line[7..line.len() - 1];
            let poly_str = line;
            let poly = get_poly(poly_str, &var_map);

            // Perform factorization.
            let instant = Instant::now();
            let factors = poly.factor();
            let elapsed = instant.elapsed();

            // Write the elapsed time and result.
            let mut monomial_factor = poly.one();
            for (f, p) in &factors {
                if f.nterms() == 1 {
                    monomial_factor = monomial_factor * &f.pow(*p);
                }
            }
            write!(
                &mut output,
                "{}.{:06}",
                elapsed.as_secs(),
                elapsed.subsec_micros()
            )
            .unwrap();
            if !monomial_factor.is_one() {
                write!(&mut output, ",{}", monomial_factor).unwrap();
            }
            for (f, p) in factors {
                if f.nterms() != 1 {
                    if p == 1 {
                        write!(&mut output, ",{}", f).unwrap();
                    } else {
                        write!(&mut output, ",({})^{}", f, p).unwrap();
                    }
                }
            }
            writeln!(&mut output).unwrap();
        } else {
            panic!("unsupported problem type");
        }
    }
}

fn get_poly(expr: &str, var_map: &Arc<Vec<Variable>>) -> MultivariatePolynomial<Z, u8> {
    parse!(expr)
        .unwrap()
        .to_polynomial(&Z, Some(var_map.clone()))
}
