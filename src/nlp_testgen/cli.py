import argparse
from nlp_testgen.parser.spec_parser import SpecParser
from nlp_testgen.generator.test_generator import TestGenerator

def main():
    parser = argparse.ArgumentParser(description="NLP Test Case Generator")
    parser.add_argument("--spec", type=str, help="The NL requirement string")
    args = parser.parse_args()

    if args.spec:
        # 1. Parse
        sp = SpecParser()
        parsed = sp.parse(args.spec)
        
        # 2. Generate
        tg = TestGenerator()
        cases = tg.generate_boundary_cases(parsed)
        
        print(f"Generated {len(cases)} test cases for: {args.spec}")
        for c in cases:
            print(f"- {c['desc']}: Input = {c['val']}")

if __name__ == "__main__":
    main()