# lifelynx/core/ai/chatbot_simple.py
import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib
import os

class LifelynxAISimple:
    def __init__(self):
        self.disease_data = self._load_disease_data()
        self.symptom_mapping = self._load_symptom_mapping()
        self.model = None
        self.model_path = os.path.join(os.path.dirname(__file__), 'lifelynx_model.joblib')
        self._initialize_model()
        
    def _load_disease_data(self):
        """Load comprehensive disease database for Nigerian context"""
        return {
            'malaria': {
                'symptoms': ['fever', 'headache', 'body pain', 'chills', 'sweating', 'hot body', 'joint pain'],
                'treatment': 'Artemisinin-based combination therapy',
                'emergency_level': 2,
                'drugs': ['Artemisinin', 'Chloroquine', 'Quinine', 'Paracetamol'],
                'description': 'Mosquito-borne disease common in Nigeria'
            },
            'typhoid': {
                'symptoms': ['fever', 'stomach pain', 'headache', 'loss of appetite', 'belle pain', 'weakness'],
                'treatment': 'Ciprofloxacin or Azithromycin',
                'emergency_level': 3,
                'drugs': ['Ciprofloxacin', 'Azithromycin', 'Ceftriaxone'],
                'description': 'Bacterial infection from contaminated food/water'
            },
            'cholera': {
                'symptoms': ['diarrhea', 'vomiting', 'dehydration', 'belle run', 'dey vomit', 'thirst'],
                'treatment': 'Oral rehydration solution and antibiotics',
                'emergency_level': 4,
                'drugs': ['ORS', 'Doxycycline', 'Azithromycin'],
                'description': 'Acute diarrheal infection from contaminated water'
            },
            'lassa fever': {
                'symptoms': ['fever', 'headache', 'sore throat', 'muscle pain', 'chest pain', 'vomiting'],
                'treatment': 'Ribavirin and supportive care',
                'emergency_level': 5,
                'drugs': ['Ribavirin'],
                'description': 'Viral hemorrhagic fever common in West Africa'
            },
            'common cold': {
                'symptoms': ['cough', 'cold', 'sneezing', 'running nose', 'headache', 'sore throat'],
                'treatment': 'Rest, hydration, and symptom relief',
                'emergency_level': 1,
                'drugs': ['Paracetamol', 'Vitamin C', 'Antihistamines'],
                'description': 'Viral infection of upper respiratory tract'
            },
            'dengue fever': {
                'symptoms': ['fever', 'rash', 'muscle pain', 'joint pain', 'headache', 'eye pain'],
                'treatment': 'Symptomatic treatment and hydration',
                'emergency_level': 3,
                'drugs': ['Paracetamol', 'IV fluids'],
                'description': 'Mosquito-borne viral infection'
            },
            'urinary tract infection': {
                'symptoms': ['painful urination', 'frequent urination', 'stomach pain', 'fever'],
                'treatment': 'Antibiotics and hydration',
                'emergency_level': 2,
                'drugs': ['Ciprofloxacin', 'Nitrofurantoin'],
                'description': 'Infection in urinary system'
            },
            'pneumonia': {
                'symptoms': ['cough', 'fever', 'chest pain', 'difficulty breathing', 'fatigue'],
                'treatment': 'Antibiotics and respiratory support',
                'emergency_level': 4,
                'drugs': ['Amoxicillin', 'Azithromycin'],
                'description': 'Lung infection causing inflammation'
            }
        }
    
    def _load_symptom_mapping(self):
        """Multi-language symptom keyword mapping for Nigerian languages"""
        return {
            'fever': {
                'english': ['fever', 'temperature', 'hot', 'burning up'],
                'pidgin': ['dey hot', 'body hot', 'fever', 'temperature dey high', 'my body dey burn me'],
                'yoruba': ['iba', 'ooru ara', 'gbona', 'ara n gbona'],
                'igbo': ['ahu oku', 'fiva', 'oku ahu', 'ahu na-ere oku'],
                'hausa': ['zazzabi', 'sanyi', 'yana da zafi', 'jiki yana zafi']
            },
            'headache': {
                'english': ['headache', 'head pain', 'migraine'],
                'pidgin': ['head dey pain me', 'my head dey hurt', 'headache', 'my head heavy'],
                'yoruba': ['ori fifo', 'ori n dun', 'ori wiwo'],
                'igbo': ['isi oku', 'isi na-egbu mgbu', 'isi ihe'],
                'hausa': ['ciwon kai', 'kai yana ciwo', 'kai nauyi']
            },
            'stomach_pain': {
                'english': ['stomach pain', 'belly pain', 'abdominal pain'],
                'pidgin': ['belle dey pain', 'stomach dey hurt', 'my belle', 'belle pain'],
                'yoruba': ['inu n dun', 'afia', 'inu fifo', 'ikun n dun'],
                'igbo': ['afo na-egbu mgbu', 'afo oku', 'afo ihe'],
                'hausa': ['ciwon ciki', 'ciki yana ciwo', 'ciki zafi']
            },
            'vomiting': {
                'english': ['vomiting', 'throwing up', 'nausea'],
                'pidgin': ['dey vomit', 'I dey vomit', 'feel like to vomit', 'my belle dey turn'],
                'yoruba': ['sisun', 'ma a sun', 'okan n mi', 'ife mi n sun'],
                'igbo': ['agbu olu', 'ichota', 'ulo ara', 'agwo olu'],
                'hausa': ['amai', 'yana amai', 'jin amai', 'hana amai']
            },
            'diarrhea': {
                'english': ['diarrhea', 'running stomach', 'loose stool'],
                'pidgin': ['belle run', 'dey run belle', 'watery stool', 'my belle dey run water'],
                'yoruba': ['iju isan', 'isan', 'inu n san', 'igbe'],
                'igbo': ['afo ojoo', 'isia afo', 'afo na-agu mmiri'],
                'hausa': ['zawo', 'cikin yana zawo', 'gudawa']
            },
            'cough': {
                'english': ['cough', 'coughing', 'chesty cough'],
                'pidgin': ['dey cough', 'cough dey worry me', 'my cough no dey stop'],
                'yoruba': ['ikō', 'ikō n pa mi', 'ikō pipe'],
                'igbo': ['ukwu', 'ukwu na-egbu m', 'ukwu oku'],
                'hausa': ['tari', 'tari yana damuna', 'tari mai zafi']
            },
            'body_pain': {
                'english': ['body pain', 'muscle pain', 'joint pain'],
                'pidgin': ['my body dey pain me', 'all my body dey hurt', 'joint dey pain'],
                'yoruba': ['ara n dun', 'egungun n dun', 'ara gbogbo n dun'],
                'igbo': ['ahu na-egbu mgbu', 'oku ahu', 'mgbu ahu'],
                'hausa': ['ciwon jiki', 'jiki yana ciwo', 'ciwon tsokaci']
            },
            'weakness': {
                'english': ['weakness', 'fatigue', 'tiredness'],
                'pidgin': ['I dey weak', 'no strength', 'my body no get power'],
                'yoruba': ['ailekun', 'alailera', 'ara fe'],
                'igbo': ['ume adighi ike', 'ike agwula', 'ahu adighi ike'],
                'hausa': ['rashin karfi', 'gajiya', 'kasala']
            }
        }
    
    def _create_training_data(self):
        """Create comprehensive training data for the ML model"""
        texts = []
        labels = []
        
        # Training examples for each disease
        training_examples = [
            # Malaria
            ("I have fever and headache", "malaria"),
            ("My body is hot and I have body pain", "malaria"),
            ("I dey hot and my head dey pain me", "malaria"),
            ("Fever with chills and sweating", "malaria"),
            ("I have high temperature and joint pain", "malaria"),
            
            # Typhoid
            ("My belle dey pain and I dey vomit", "typhoid"),
            ("Stomach pain with fever and weakness", "typhoid"),
            ("I have stomach pain and loss of appetite", "typhoid"),
            ("Belle pain with high temperature", "typhoid"),
            
            # Cholera
            ("I dey run belle and dey vomit", "cholera"),
            ("Diarrhea and vomiting with dehydration", "cholera"),
            ("Watery stool and stomach cramps", "cholera"),
            ("Belle run and I dey feel weak", "cholera"),
            
            # Lassa Fever
            ("Fever with sore throat and muscle pain", "lassa fever"),
            ("High temperature with chest pain and vomiting", "lassa fever"),
            ("I dey hot with throat pain and body pain", "lassa fever"),
            
            # Common Cold
            ("I have cough and running nose", "common cold"),
            ("I dey cough and cold dey worry me", "common cold"),
            ("Cough with headache and sneezing", "common cold"),
            ("Running nose with sore throat", "common cold"),
            
            # Dengue Fever
            ("Fever with rash and muscle pain", "dengue fever"),
            ("High temperature with joint pain and eye pain", "dengue fever"),
            
            # UTI
            ("Pain when I urinate and stomach pain", "urinary tract infection"),
            ("I dey piss and e dey pain me", "urinary tract infection"),
            ("Frequent urination with pain", "urinary tract infection"),
            
            # Pneumonia
            ("Cough with chest pain and fever", "pneumonia"),
            ("I dey cough and my chest dey pain me", "pneumonia"),
            ("Difficulty breathing with cough", "pneumonia"),
        ]
        
        for text, label in training_examples:
            texts.append(text)
            labels.append(label)
        
        return texts, labels
    
    def _initialize_model(self):
        """Initialize or load the ML model"""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("Loaded trained model from disk")
            except:
                print("Failed to load model, training new one")
                self._train_and_save_model()
        else:
            self._train_and_save_model()
    
    def _train_and_save_model(self):
        """Train the model and save it to disk"""
        try:
            texts, labels = self._create_training_data()
            
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=1000, stop_words='english')),
                ('clf', MultinomialNB(alpha=0.1))
            ])
            
            self.model.fit(texts, labels)
            joblib.dump(self.model, self.model_path)
            print("AI model trained and saved successfully")
        except Exception as e:
            print(f"Model training failed: {e}")
            self.model = None
    
    def preprocess_text(self, text, language):
        """Clean and preprocess input text"""
        text = text.lower().strip()
        
        # Language-specific preprocessing
        filler_words = {
            'pidgin': ['na wa o', 'eiyah', 'abeg', 'o', 'sha', 'please', 'help'],
            'yoruba': ['e ma binu', 'jowo', 'o', 'd', 'se'],
            'igbo': ['biko', 'o', 'nwannem', 'kedu'],
            'hausa': ['allah', 'don allah', 'yaya', 'kai'],
            'english': ['please', 'help', 'hello', 'hi', 'hey']
        }
        
        words = filler_words.get(language, [])
        for word in words:
            text = text.replace(word, '')
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_symptoms(self, text, language='english'):
        """Extract symptoms from user input using multi-language mapping"""
        text = self.preprocess_text(text, language)
        detected_symptoms = []
        
        for symptom, keywords in self.symptom_mapping.items():
            lang_keywords = keywords.get(language, keywords['english'])
            if any(keyword in text for keyword in lang_keywords):
                detected_symptoms.append(symptom)
        
        return detected_symptoms
    
    def diagnose(self, symptoms, text_input):
        """Generate diagnosis based on symptoms and text input"""
        possible_diseases = []
        
        # Rule-based diagnosis first
        for disease, data in self.disease_data.items():
            disease_symptoms = data['symptoms']
            matches = len(set(symptoms) & set(disease_symptoms))
            total_symptoms = len(disease_symptoms)
            
            if total_symptoms > 0:
                confidence = matches / total_symptoms
                
                # Boost confidence for key symptoms
                key_symptoms = disease_symptoms[:3]  # First 3 symptoms are key
                key_matches = len(set(symptoms) & set(key_symptoms))
                if key_matches > 0:
                    confidence += 0.3
                
                # Minimum 2 symptoms or key symptom for reliable diagnosis
                if confidence > 0.3 and (matches >= 2 or key_matches > 0):
                    possible_diseases.append({
                        'disease': disease,
                        'confidence': min(round(confidence, 2), 0.95),
                        'emergency_level': data['emergency_level'],
                        'treatment': data['treatment'],
                        'recommended_drugs': data['drugs'],
                        'description': data['description']
                    })
        
        # Use ML model for additional insight
        if self.model and text_input and len(text_input) > 10:
            try:
                ml_prediction = self.model.predict([text_input])[0]
                ml_prob = self.model.predict_proba([text_input]).max()
                
                # Only use ML if confidence is high and not already in list
                if ml_prob > 0.7 and not any(d['disease'] == ml_prediction for d in possible_diseases):
                    disease_data = self.disease_data.get(ml_prediction, {})
                    possible_diseases.append({
                        'disease': ml_prediction,
                        'confidence': round(ml_prob, 2),
                        'emergency_level': disease_data.get('emergency_level', 1),
                        'treatment': disease_data.get('treatment', 'Consult doctor'),
                        'recommended_drugs': disease_data.get('drugs', []),
                        'description': disease_data.get('description', '')
                    })
            except Exception as e:
                print(f"ML prediction error: {e}")
        
        # Sort by confidence and emergency level
        possible_diseases.sort(key=lambda x: (x['confidence'], -x['emergency_level']), reverse=True)
        return possible_diseases
    
    def check_emergency(self, symptoms, diagnosis):
        """Check if the situation requires emergency attention"""
        # High fever emergency
        if any('hot' in symptom or 'fever' in symptom for symptom in symptoms) and len(symptoms) > 3:
            return True
        
        # Severe symptoms
        severe_symptoms = ['difficulty breathing', 'chest pain', 'severe dehydration', 'unconscious']
        if any(symptom in severe_symptoms for symptom in symptoms):
            return True
        
        # High emergency level diagnosis
        if diagnosis and any(d['emergency_level'] >= 4 for d in diagnosis):
            return True
        
        return False
    
    def generate_response(self, user_input, user_language='pidgin', user_context=None):
        """Main method to process user input and generate response"""
        try:
            # Extract symptoms
            symptoms = self.extract_symptoms(user_input, user_language)
            
            # Generate diagnosis
            diagnosis_results = self.diagnose(symptoms, user_input)
            
            # Check for emergency
            is_emergency = self.check_emergency(symptoms, diagnosis_results)
            
            # Format response based on language
            response = self._format_response(
                diagnosis_results, 
                user_language, 
                symptoms,
                is_emergency
            )
            
            return {
                'symptoms_detected': symptoms,
                'diagnosis': diagnosis_results,
                'response': response,
                'is_emergency': is_emergency
            }
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                'symptoms_detected': [],
                'diagnosis': [],
                'response': self._get_error_message(user_language),
                'is_emergency': False
            }
    
    def _get_error_message(self, language):
        """Get error message in appropriate language"""
        messages = {
            'pidgin': "System dey busy now. Try again small time.",
            'english': "System is busy right now. Please try again later.",
            'yoruba': "Sistemi wa ni isisẹ bayi. Jowo gbiyanju lẹẹkansi.",
            'igbo': "Sistemu nọ n'ọrụ ugbu a. Biko nwaa ọzọ.",
            'hausa': "Tsarin yana aiki yanzu. Don Allah a sake ƙoƙari."
        }
        return messages.get(language, messages['english'])
    
    def _format_response(self, diagnosis, language, symptoms, is_emergency):
        """Format response in user's preferred language"""
        if is_emergency:
            return self._format_emergency_response(language)
        
        if not diagnosis:
            return self._get_no_diagnosis_message(language, symptoms)
        
        top_diagnosis = diagnosis[0]
        return self._format_diagnosis_response(top_diagnosis, language)
    
    def _format_emergency_response(self, language):
        """Format emergency response"""
        messages = {
            'pidgin': "🚨 EMERGENCY! This one serious o! Make you go hospital NOW NOW! I don alert emergency services. Type OKADA make we book bike for you quick quick!",
            'english': "🚨 EMERGENCY! This is serious! Please go to the hospital IMMEDIATELY! I've alerted emergency services. Type OKADA to book immediate transportation!",
            'yoruba': "🚨 IJAMBA! Eleyi ko duro! Jowo lọ si ile iwosan NI KIAKIA! Mo ti fi ijiyan sile. Tẹ OKADA lati fi okada sakoko!",
            'igbo': "🚨 IHE MKPA! Nke a dị oke egwu! Biko gaa ụlọ ọgwụ NGWA NGWA! Emeela m ndị ọrụ mberede. Pịa OKADA iji nye ụgbọ ala ọkwa ngwa ngwa!",
            'hausa': "🚨 GAGGAVA! Wannan yana da muhimmanci! Don Allah a je asibiti YANZU! Na gargaɗi ayyukan gaggawa. Danna OKADA don yin aikin motar da sauri!"
        }
        return messages.get(language, messages['english'])
    
    def _get_no_diagnosis_message(self, language, symptoms):
        """Message when no diagnosis can be made"""
        if symptoms:
            messages = {
                'pidgin': f"No worry, I dey your back. From your symptoms ({', '.join(symptoms)}), make you rest well and drink plenty water. If you no better in 24 hours, type OKADA make we find hospital for you.",
                'english': f"Don't worry, I'm here to help. Based on your symptoms ({', '.join(symptoms)}), please rest well and drink plenty of water. If you don't feel better in 24 hours, type OKADA to find a hospital.",
                'yoruba': f"Ma binu, mo wa nibi lati ran yin lowo. Lati inu awọn aami rẹ ({', '.join(symptoms)}), jowo sinmi daradara ki o mu omi pupo. Ti o ko ba gba ni wakati 24, tẹ OKADA lati wa ile iwosan.",
                'igbo': f"Echegbula, anọ m ebe a iji nyere gị aka. Dabere na ihe mgbaàmà gị ({', '.join(symptoms)}), biko zuru ike ma ṅụọ mmiri. Ọ bụrụ na ị naghị enwe mma n'ime awa 24, pịa OKADA iji chọta ụlọ ọgwụ.",
                'hausa': f"Kada ku damu, ina nan don taimakon ku. Daga alamun ku ({', '.join(symptoms)}), don Allah a huta da kyau, ku sha ruwa da yawa. Idan ba ku ji dadi a cikin sa'o'i 24, danna OKADA don nemo asibiti."
            }
        else:
            messages = {
                'pidgin': "No worry, I dey your back. But from wetin you talk, I no too sure wetin dey. Make you try explain am better or go see doctor.",
                'english': "Don't worry, I'm here to help. But from what you described, I'm not sure what's wrong. Please try to explain better or see a doctor.",
                'yoruba': "Ma binu, mo wa nibi lati ran yin lowo. Sugbon nipa ohun ti o so, mi o da loruko ohun ti o n sele. Jowo gbiyanju lati salaye si daradara tabi lo si dokita.",
                'igbo': "Echegbula, anọ m ebe a iji nyere gị aka. Mana site n'ihe ị kọwara, amaghị m ihe na-eme. Biko nwaa ịkọwa nke ọma ma ọ bụ gaa dọkịta.",
                'hausa': "Kada ku damu, ina nan don taimakon ku. Amma daga abin da kuka bayyana, ban san abin da ke faruwa ba. Don Allah a yi ƙoƙari ku bayyana da kyau ko ku je likita."
            }
        return messages.get(language, messages['english'])
    
    def _format_diagnosis_response(self, diagnosis, language):
        """Format diagnosis response"""
        disease = diagnosis['disease']
        confidence = diagnosis['confidence']
        drugs = diagnosis['recommended_drugs']
        description = diagnosis.get('description', '')
        
        drug_text = drugs[0] if drugs else "appropriate medication"
        
        if confidence > 0.7:
            templates = {
                'pidgin': f"Eiyah sorry o! You fit get {disease}. {description} Make you go PHC wey get {drug_text} now now! Type OKADA make driver come your side.",
                'english': f"I'm sorry! You might have {disease}. {description} Please visit a PHC that has {drug_text}. Type OKADA to book transportation.",
                'yoruba': f"E ma binu! O le ni {disease}. {description} Jowo lo si PHC ti o ni {drug_text}. Teko OKADA lati fi okada sakoko.",
                'igbo': f"Ndo! I nwere ike inwe {disease}. {description} Biko gaa PHC nwere {drug_text}. Pịa OKADA iji nye ụgbọ ala ọkwa.",
                'hausa': f"Yi hakuri! Kuna iya samun {disease}. {description} Don Allah a ziyarci PHC wanda yake da {drug_text}. Latsa OKADA don yin aikin motar."
            }
        elif confidence > 0.5:
            templates = {
                'pidgin': f"No worry, but you fit get {disease}. {description} Make you rest well, drink plenty water. If you no better, type OKADA make we help you find PHC wey get {drug_text}.",
                'english': f"Don't worry, but you might have {disease}. {description} Please rest well and drink plenty of water. If you don't feel better, type OKADA to find a PHC with {drug_text}.",
                'yoruba': f"Ma binu, sugbon o le ni {disease}. {description} Jowo sun won, mu omi pupo. Ti o ko ba gba, te OKADA lati wa PHC ti o ni {drug_text}.",
                'igbo': f"Echegbula, mana i nwere ike inwe {disease}. {description} Biko zuru ike ma ṅụọ mmiri. Ọ bụrụ na ị naghị enwe mma, pịa OKADA iji chọta PHC nwere {drug_text}.",
                'hausa': f"Kada ku damu, amma kuna iya samun {disease}. {description} Don Allah a huta da kyau, ku sha ruwa da yawa. Idan ba ku ji dadi ba, danna OKADA don nemo PHC mai {drug_text}."
            }
        else:
            templates = {
                'pidgin': f"Small small, you fit get {disease}. {description} Make you observe your body well. If e worse or you no better tomorrow, type OKADA make we book bike for you.",
                'english': f"There's a slight chance you might have {disease}. {description} Please monitor your symptoms. If they worsen or you don't feel better tomorrow, type OKADA.",
                'yoruba': f"Kekere, o le ni {disease}. {description} Jowo wo awọn aami ara rẹ daradara. Ti o ba buru tabi o ko ba gba ni ola, te OKADA.",
                'igbo': f"O nwere ohere pere mpe na ị nwere ike inwe {disease}. {description} Biko nyochaa ihe mgbaàmà gị. Ọ bụrụ na ha akawanye njọ ma ọ bụ na ị naghị enwe mma echi, pịa OKADA.",
                'hausa': f"Akwai ɗan dama kuna iya samun {disease}. {description} Don Allah a lura da alamun ku. Idan sun yi muni ko ba ku ji dadi gobe, danna OKADA."
            }
        
        return templates.get(language, templates['english'])