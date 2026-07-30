import argparse
import fractions
import operator
import pint

def valid_number(value):
    try:
        return fractions.Fraction(value)
    except (ValueError, ZeroDivisionError):
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a valid numerical input."
        )
    
def make_display(value, as_fraction = False):
    if as_fraction:
        return str(value)

    if value.denominator == 1:
        return str(value.numerator)

    return format(float(value), ".12g")

ureg = pint.UnitRegistry(non_int_type=fractions.Fraction)
pint_units = list(ureg)

parser = argparse.ArgumentParser(description="Simple Calculator CLI")
subparsers = parser.add_subparsers(dest="mode", help="Program mode")


calc_parser = subparsers.add_parser("calculate", help="Arithmetic mode")
calc_parser.add_argument("numberOne", type=valid_number, help="First numerical input")
calc_parser.add_argument("operation", choices=["plus", "minus", "times", "over"], help="Operation")
calc_parser.add_argument("numberTwo", type=valid_number, help="Second numerical input")
calc_parser.add_argument("--fraction", action="store_true", help="Return the result as a fraction")

convert_parser = subparsers.add_parser("convert", help="Unit conversion mode")
convert_parser.add_argument("inputValue", type=valid_number, help="Input value")
convert_parser.add_argument("inputUnit", choices=pint_units, help="Input unit")
convert_parser.add_argument("outputUnit", choices=pint_units, help="Output unit")
convert_parser.add_argument("--fraction", action="store_true", help="Return the result as a fraction")

args = parser.parse_args()

if args.mode == "calculate":
    operations = {
        "plus": operator.add,
        "minus": operator.sub,
        "times": operator.mul,
        "over": operator.truediv,
    }

    if args.operation == "over" and args.numberTwo == 0:
        parser.error("Cannot divide by zero.")

    result = operations[args.operation](args.numberOne, args.numberTwo)
    print(make_display(result, as_fraction=args.fraction))


elif args.mode == "convert":
    try:
        quantity = ureg.Quantity(args.inputValue, args.inputUnit)
        result = quantity.to(args.outputUnit)
        magnitude = make_display(result.magnitude, args.fraction)

        print(magnitude, result.units)

    except pint.errors.UndefinedUnitError as error:
        convert_parser.error(f"Unknown unit: {error}")

    except pint.errors.DimensionalityError:
        convert_parser.error(
            f"Cannot convert {args.inputUnit} to {args.outputUnit}"
        )