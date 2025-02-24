class Patient:
    def __init__(self, id, name, dob, sex, height, weight, smoking, 
                 asa=None, comiBackPain=None, comiLegPain=None, comiFunction=None,
                 comiWellbeing=None, comiQol=None, comiWorkDisability=None,
                 comiSocialDisability=None):
        self.id = id
        self.name = name
        self.dob = dob
        self.sex = sex
        self.height = height
        self.weight = weight
        self.smoking = smoking
        self.asa = asa
        self.comiBackPain = comiBackPain
        self.comiLegPain = comiLegPain
        self.comiFunction = comiFunction
        self.comiWellbeing = comiWellbeing
        self.comiQol = comiQol
        self.comiWorkDisability = comiWorkDisability
        self.comiSocialDisability = comiSocialDisability

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "dob": self.dob,
            "sex": self.sex,
            "height": self.height,
            "weight": self.weight,
            "smoking": self.smoking,
            "asa": self.asa,
            "comiBackPain": self.comiBackPain,
            "comiLegPain": self.comiLegPain,
            "comiFunction": self.comiFunction,
            "comiWellbeing": self.comiWellbeing,
            "comiQol": self.comiQol,
            "comiWorkDisability": self.comiWorkDisability,
            "comiSocialDisability": self.comiSocialDisability
        }

# Mock database with expanded patient data
MOCK_PATIENTS = [
    Patient("P001", "John Doe", "1959-03-15", "M", 175, 82, "Former", 
            "2", "7", "5", "6", "3", "2", "1", "2"),
    Patient("P002", "Erika Mustermann", "1981-11-23", "F", 162, 58, "Never",
            "1", "4", "3", "3", "1", "1", "0", "1"),
    Patient("P003", "János Kovács", "1947-07-30", "M", 180, 95, "Current",
            "3", "8", "8", "7", "4", "3", "4", "3"),
    Patient("P004", "Mario Rossi", "1990-09-05", "M", 168, 63, "Never",
            "1", "2", "1", "2", "1", "0", "0", "0")
]

def get_all_patients():
    return [patient.to_dict() for patient in MOCK_PATIENTS]

def get_patient_by_id(patient_id):
    patient = next((p for p in MOCK_PATIENTS if p.id == patient_id), None)
    return patient.to_dict() if patient else None