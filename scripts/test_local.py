"""Local testing script for CHIEF"""
import sys
sys.path.insert(0, '.')

from src.agent.orchestrator import process_message

def main():
    print("CHIEF Assistant - Local Test")
    print("Type 'quit' to exit\n")
    
    history = []
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'quit':
            print("Goodbye, Chief!")
            break
        
        if not user_input:
            continue
        
        response = process_message(user_input, history)
        print(f"\nCHIEF: {response}\n")
        
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
