#!/usr/bin/env python3
"""
LLM-Powered Test Case Generator
Pure AI-driven test generation using Llama
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def generate_tests(requirement, test_type="all"):
    """Generate test cases for a requirement."""
    try:
        from src.nlp_testgen.parser.spec_parser import SpecParser
        from src.nlp_testgen.generator.test_generator import TestGenerator
        
        print(f"\n{'='*70}")
        print(f"🤖 LLM-POWERED TEST CASE GENERATOR")
        print(f"{'='*70}")
        print(f"\n📋 Requirement: {requirement}")
        
        # Step 1: Parse with LLM
        print(f"\n[1/2] 🔍 Parsing requirement with AI...")
        parser = SpecParser()
        spec = parser.parse(requirement)
        
        print(f"\n✅ Parsed Specification:")
        print(f"   Min:         {spec.get('min', 'N/A')}")
        print(f"   Max:         {spec.get('max', 'N/A')}")
        print(f"   Data Type:   {spec.get('data_type', 'N/A')}")
        print(f"   Constraints: {spec.get('constraints', [])}")
        
        # Step 2: Generate tests with LLM
        print(f"\n[2/2] 🧪 Generating test cases with AI...")
        generator = TestGenerator()
        test_cases = generator.generate_test_cases(spec, test_type)
        
        print(f"\n{'='*70}")
        print("📝 GENERATED TEST CASES")
        print(f"{'='*70}\n")
        print(test_cases)
        print(f"\n{'='*70}")
        print("✅ Test generation completed!")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Login to HuggingFace:")
        print("      pip install huggingface-hub")
        print("      huggingface-cli login")
        print("\n   2. Accept Llama license:")
        print("      https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct")
        print()


def interactive_mode():
    """Run in interactive mode."""
    print("="*70)
    print("🤖 LLM-POWERED TEST CASE GENERATOR")
    print("="*70)
    print("\n✨ Using AI to generate intelligent test cases")
    print("\n📖 Commands:")
    print("   • Enter requirement to generate tests")
    print("   • Type 'boundary' for boundary tests only")
    print("   • Type 'security' for security tests only")
    print("   • Type 'edge' for edge case tests only")
    print("   • Type 'help' for examples")
    print("   • Type 'exit' to quit")
    print("="*70)
    
    test_type = "all"
    
    while True:
        try:
            user_input = input("\n💬 Enter requirement (or command): ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            if user_input.lower() == 'help':
                print("\n📚 Example Requirements:")
                print("   • Age must be between 18 and 65")
                print("   • Password 8-20 characters with special chars")
                print("   • Port number 1 to 65535")
                print("   • Username field for login security")
                print("   • Temperature reading -40 to 125 degrees")
                print("   • Age between 45 and 78 divisible by 2")
                continue
            
            if user_input.lower() == 'boundary':
                test_type = 'boundary'
                print("✅ Mode set to: Boundary tests only")
                continue
            
            if user_input.lower() == 'security':
                test_type = 'security'
                print("✅ Mode set to: Security tests only")
                continue
            
            if user_input.lower() == 'edge':
                test_type = 'edge'
                print("✅ Mode set to: Edge case tests only")
                continue
            
            if user_input.lower() == 'all':
                test_type = 'all'
                print("✅ Mode set to: All test types")
                continue
            
            # Generate tests
            generate_tests(user_input, test_type)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Command line mode
        requirement = " ".join(sys.argv[1:])
        generate_tests(requirement)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()