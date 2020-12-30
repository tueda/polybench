use std::env;
use std::fs::File;
use std::io::Write;
use std::io::{BufRead, BufReader, LineWriter};
use std::str::FromStr;
use std::time::Instant;

use reform::poly::polynomial::{PolyPrinter, Polynomial};
use reform::structure::{Element, VarInfo};

fn main() {
    let args: Vec<_> = env::args().collect();

    let variables = args[1].split(',');
    let input_filename = &args[2];
    let output_filename = &args[3];

    let mut var_info = VarInfo::new();
    // Register the variables in the given ordering.
    for x in variables {
        Element::<String>::from_str(x)
            .unwrap()
            .to_element(&mut var_info);
    }

    let input_file = File::open(input_filename).unwrap();
    let output_file = File::create(output_filename).unwrap();

    let mut output = LineWriter::new(output_file);

    for line in BufReader::new(input_file).lines() {
        let mut line = line.unwrap();

        if line.starts_with("gcd") {
            // The format is "gcd(poly1,poly2)". Extract poly1 and poly2.
            line.pop();
            let line = &line[4..];
            let polys: Vec<_> = line.split(',').collect();
            let mut poly1 = get_poly(polys[0], &mut var_info);
            let mut poly2 = get_poly(polys[1], &mut var_info);

            // Compute the GCD.
            let instant = Instant::now();
            let gcd = poly1.gcd(&mut poly2);
            let elapsed = instant.elapsed();

            // Write the elapsed time and result.
            writeln!(
                &mut output,
                "{}.{:06},{}",
                elapsed.as_secs(),
                elapsed.subsec_micros(),
                PolyPrinter {
                    poly: &gcd,
                    var_info: &var_info.global_info
                }
            )
            .unwrap();
        } else {
            panic!("unsupported problem type");
        }
    }
}

fn get_poly(expr: &str, var_info: &mut VarInfo) -> Polynomial {
    let mut e = Element::<String>::from_str(expr).unwrap();
    let mut ne = e.to_element(var_info);
    ne.normalize_inplace(&var_info.global_info);
    Polynomial::from(&ne).unwrap()
}
