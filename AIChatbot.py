print("My First AI Chatbot")

import nltk
from nltk.tokenize import word_tokenize

from datetime import datetime
time = datetime.now().strftime("%Y-%m-%d %I:%M %p")

nltk.download('punkt')


responses = {
    'hi': 'Hi, how are you today?',
    'jambo': 'Mzuri sana, nikusaidie vipi leo?',
    'mambo': 'Niko poa sana, niambie',
    'nataka':'Tafadhali tumia lugha ya heshima kama tafadhali, naomba, nisaidie...',
    
    'how are': 'I am doing well, how about you?',
    'know': 'I can attempt to respond to that',
    'time': 'Hi today is...getting you info',
    'fine': 'Great to hear you are doing well.',
    'well': 'Nice to hear!',
    'about you': 'I am a simple chatbot to keep you engaged.',
    'ai': 'I am an AI based Chatbot.',
    'what': 'I am here to assist you. Ask me anything today',
    'about': 'I exist in the digital world.',
    'made': ' I was made in Kenya and I am always available.',
    'when were you': 'Am sorry I cannot give specific time',
    'computer': 'I am an artificial intelligent software developed to answer your questions',
    'kenya': 'Kenya is a country in Eastern Africa, with bright and humourous people in the world',
    'china': 'China is an Asian country with highest global GDP and most advanced technology in the world.',
    'country': 'Which country do you want to get information about?',
    'why': 'Because I was created to help.',
    'work': 'I operate based on predefined responses.',
    'game': 'Sure! we can play a game. Can play you a song',
    
    'exit': 'Goodbye! Have a great day.',
    'want': 'I am sorry am still in development phase to answer that.'
    
}

def generate_response(user_input):
    tokens = word_tokenize(user_input.lower())
    for token in tokens:
        if token in responses:
            return responses[token]
    return "Sorry, I don't understand that question."


while True:
    user_input = input("You: ")
    if user_input.lower() == 'exit':
        print("Bot:", responses['exit'])
        break
    response = generate_response(user_input)
    print("Bot:", response)
    