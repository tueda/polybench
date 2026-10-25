"""Poly Mojo bridge; input decoding and output encoding are untimed."""
from apn_mojo import Integer
from poly import sparse, exact
from std.sys import argv, get_defined_int
from std.time import perf_counter_ns

comptime NVARS = get_defined_int["NVARS", 2]()


struct Reader(Movable):
    var text: String
    var position: Int

    def __init__(out self, var text: String):
        self.text = text^
        self.position = 0

    def number(mut self) raises -> Int:
        var end = self.text.find("\n", self.position)
        if end < 0:
            raise Error("truncated integer in polybench input")
        var value = Int(String(self.text[byte=self.position:end]))
        self.position = end + 1
        return value

    def record(mut self) raises -> String:
        var size = self.number()
        if size < 0 or size > self.text.byte_length() - self.position:
            raise Error("truncated polynomial in polybench input")
        var value = String(self.text[byte=self.position:self.position + size])
        self.position += size
        return value


def packed[P: Copyable & Deinitable, k: Int](p: sparse.Array[P, k]) raises -> String:
    var text = sparse.dumps(p)
    return String(text.byte_length(), "\n", text)


def factored[P: Copyable & Deinitable](
    unit: Integer, factors: List[Tuple[sparse.Array[P, 0], Int]]
) raises -> String:
    var text = String(unit, "\n", len(factors), "\n")
    for entry in factors:
        text.write(entry[1], "\n", packed(entry[0]))
    return text^


def main() raises:
    var args = List[String]()
    for item in argv():
        args.append(String(item))
    if len(args) != 5:
        raise Error("usage: driver gcd|factor INPUT OUTPUT plain|certified")
    if args[1] != "gcd" and args[1] != "factor":
        raise Error("unsupported operation")
    if args[4] != "plain" and args[4] != "certified":
        raise Error("unsupported certificate mode")
    var certified = args[4] == "certified"
    var reader = Reader(open(args[2], "r").read())
    var count = reader.number()
    if count < 0:
        raise Error("negative problem count")
    with open(args[3], "w") as output:
        output.write(String(count, "\n"))
        for _ in range(count):
            var a = sparse.loads[Integer, ndim=NVARS](reader.record())
            var elapsed = 0
            var check_ns = 0
            var payload = String()
            if args[1] == "gcd":
                var b = sparse.loads[Integer, ndim=NVARS](reader.record())
                if certified:
                    var start = perf_counter_ns()
                    var result = sparse.gcd_checked(a, b)
                    elapsed = Int(perf_counter_ns() - start)
                    start = perf_counter_ns()
                    var valid = exact.check(result)
                    check_ns = Int(perf_counter_ns() - start)
                    if not valid:
                        raise Error("GCD certificate verification failed")
                    payload = String("1\n1\n1\n", packed(exact.value(result)))
                else:
                    var start = perf_counter_ns()
                    var result = sparse.gcd(a, b)
                    elapsed = Int(perf_counter_ns() - start)
                    payload = String("1\n1\n1\n", packed(result))
            else:
                if certified:
                    var start = perf_counter_ns()
                    var result = sparse.factor_checked(a)
                    elapsed = Int(perf_counter_ns() - start)
                    start = perf_counter_ns()
                    var valid = exact.check(result)
                    check_ns = Int(perf_counter_ns() - start)
                    if not valid:
                        raise Error("factor certificate verification failed")
                    payload = factored(exact.unit(result), exact.factors(result))
                else:
                    var start = perf_counter_ns()
                    var result = sparse.factor(a)
                    elapsed = Int(perf_counter_ns() - start)
                    payload = factored(result[0], result[1])
            output.write(String(elapsed, "\n", check_ns, "\n", payload))
    if reader.position != reader.text.byte_length():
        raise Error("trailing bytes in polybench input")
