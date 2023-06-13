import os, openai

# Set openai.api_key to the OPENAI environment variable
openai.api_key = os.environ["LLAVE"]

system_msg = 'Eres un traductor de japones al español.'

def translate_text1(text):
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                        messages=[{"role": "system", "content": system_msg},
                                         {"role": "user", "content": text}])
    return response

