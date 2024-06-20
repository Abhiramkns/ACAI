import random
import os
import json
from PIL import Image
from .graph import generate_graph

QUESTIONS = {
    1: 'Where were you born?',
    2: 'Where is your hometown?',
    3: 'What is your earliest childhood memory?', 
    4: "What is your Father's name?",
    5: 'What is your favorite movie?',
    6: 'Where did you go to school?',
    7: 'What did you study?',
    8: 'What was your first job?',
    9: 'What is your hobby?',
    10: "What's your favorite book?"
}

REALTIONS = {
    1: 'Birth place',
    2: 'Hometown',
    3: 'Childhood memory',
    4: 'Father',
    5: 'Favorite movie',
    6: 'school',
    7: 'Major study',
    8: 'First job',
    9: 'Hobby',
    10: 'Favorite book'
}

class UserQuestions:
    def __init__(self, path='../../user_data'):
        self.data = {}
        if os.path.exists(f"{path}/answered_questions.json"):
            with open(f"{path}/answered_questions.json", 'r') as f:
                self.data = json.load(f)
        self.answered = set(self.data.keys())
        self.ques2id = {}
        unanswered = []
        for k, v in QUESTIONS.items():
            self.ques2id[v] = k
            if k not in self.answered:
                unanswered.append(k)
        self.unanswered = set(unanswered)

        self.path = path
        
    def get_question(self): 
        ques_id = random.choice(list(self.unanswered))
        ques = QUESTIONS[ques_id]
        return ques, ques_id
    
    def get_ques_id(self, ques):
        return self.ques2id[ques]
    
    def add_answer(self, ques, ans, files=None):
        ques_id = self.get_ques_id(ques)
        relation = REALTIONS[int(ques_id)]
        self.data[int(ques_id)] = {
            'question': ques, 
            'entity': ans,
            'relation': relation,
        }

        file_paths = []
        if files is not None:
            for i, f in enumerate(files):
                img = Image.open(f).convert('RGB')
                path = os.path.join(f"{self.path}/images", f"{ques_id}_{i}.png")
                file_paths.append(path)
                img.save(path)
        self.data[int(ques_id)]['files'] = file_paths

        self.unanswered.remove(ques_id)
    
    def save(self):
        with open(f"{self.path}/answered_questions.json", 'w') as f:
            json.dump(self.data, f)

    def generate_graph(self):
        nodes = []
        relations = []
        for node in self.data.values():
            nodes.append(node['entity'])
            relations.append(node['relation'])
        edges = []
        for i, node in enumerate(nodes):
            edges.append(['Me', node, relations[i]])
        
        nodes.append('Me')
        nodes = set(nodes)
        
        generate_graph(nodes, edges)