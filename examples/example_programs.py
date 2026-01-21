# nlp_testgen/examples/target_app.py
import sys

def check_age(age):
    try:
        age = int(age)
        if 18 <= age <= 60:
            print("Access Granted")
            return True
        else:
            print("Access Denied")
            return False
    except ValueError:
        print("Invalid Input")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_age(sys.argv[1])