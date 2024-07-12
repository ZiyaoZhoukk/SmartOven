from openai import OpenAI 
import os

def call(prompt):
  MODEL="gpt-4o"
  client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

  completion = client.chat.completions.create(
    model=MODEL,
    messages=[
      {"role": "system", "content": prompt[0]}, # <-- This is the system message that provides context to the model
      {"role": "user", "content": prompt[1]}  # <-- This is the user message for which the model will generate a response
    ]
  )

  return completion.choices[0].message.content

def main():
  system_content='You are a helpful assistant'
  user_content='what is 1+1?'
  response=call(system_content,user_content)
  print(response)

if __name__ == "__main__":
    main()