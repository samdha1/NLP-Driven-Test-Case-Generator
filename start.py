import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def generate_tests(requirement, test_type="all"):
    try:
        from src.nlp_testgen.parser.spec_parser import SpecParser
        from src.nlp_testgen.generator.test_generator import TestGenerator

        print(f" LLM-POWERED TEST CASE GENERATOR")
        print(f"\n Requirement: {requirement}")

        print(f"\n[1/2]  Parsing ...")
        parser = SpecParser()
        result = parser.parse(requirement)
        if isinstance(result, list): specs = result
        else: specs = [result]
        generator = TestGenerator()
        for i, spec in enumerate(specs):
            field_label = spec.get("field", f"Input {i+1}") if len(specs) > 1 else "Input"
            print(f"\n Parsed Specification — {field_label}:")
            print(f"   Min:         {spec.get('min', 'N/A')}")
            print(f"   Max:         {spec.get('max', 'N/A')}")
            print(f"   Data Type:   {spec.get('data_type', 'N/A')}")
            print(f"   Constraints: {spec.get('constraints', [])}")
            print(f"\n[2/2]  Generating test cases for {field_label}...")
            test_cases = generator.generate_test_cases(spec, test_type)

            print(f" GENERATED TEST CASES — {field_label}")
            print(f"\n")
            print(test_cases)
        print(" Test generation completed!")

    except Exception as e:
        print(f"\n Error: {e}")
        print("\n Troubleshooting:")
        print("   1. Login to HuggingFace:")
        print("      pip install huggingface-hub")
        print("      huggingface-cli login")
        print("\n   2. Accept Llama license:")
        print("      https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct")
        print()


def interactive_mode():
    print(" LLM-POWERED TEST CASE GENERATOR")
    test_type = "all"
    while True:
        try:
            user_input = input("\n Enter requirement (or command): ").strip()

            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n End!\n")
                break
            if user_input.lower() == 'help':
                print("\n Example Requirements:")
                print("   • Age must be between 18 and 65")
                print("   • Password 8-20 characters with special chars")
                print("   • Port number 1 to 65535")
                print("   • Username field for login security")
                print("   • Temperature reading -40 to 125 degrees")
                print("   • Age between 45 and 78 divisible by 2")
                print("\n   Multiple input examples:")
                print("   • Age between 18 and 65, password must be 8 to 20 characters")
                print("   • Score from 0 to 100; grade must be between 1 and 5")
                continue
            if user_input.lower() == 'boundary':
                test_type = 'boundary'
                print(" Mode set to: Boundary tests only")
                continue
            if user_input.lower() == 'security':
                test_type = 'security'
                print(" Mode set to: Security tests only")
                continue
            if user_input.lower() == 'edge':
                test_type = 'edge'
                print(" Mode set to: Edge case tests only")
                continue
            if user_input.lower() == 'all':
                test_type = 'all'
                print(" Mode set to: All test types")
                continue
            generate_tests(user_input, test_type)

        except KeyboardInterrupt:
            print("\n\n End!\n")
            break
        except Exception as e:
            print(f"\n Error: {e}\n")

def main():
    if len(sys.argv) > 1:
        requirement = " ".join(sys.argv[1:])
        generate_tests(requirement)
    else:
        interactive_mode()

if __name__ == "__main__":
    main()