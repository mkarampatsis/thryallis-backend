import json
from bson import ObjectId
import mongoengine as me
from src.models.upload import FileUpload
from datetime import datetime
import uuid


def default_ada():
    return f"ΜΗ ΑΝΑΡΤΗΤΕΑ ΠΡΑΞΗ-{uuid.uuid4()}"


class FEK(me.EmbeddedDocument):
    # number = me.StringField()
    # issue = me.StringField(choices=["", "Α", "Β", "Υ.Ο.Δ.Δ."])
    date = me.StringField()


class InstructionAct(me.Document):
    meta = {
        "collection": "instruction_acts",
        "db_alias": "psped",
        "indexes": [
            # {"fields": ["fek.number", "fek.issue", "fek.date"], "unique": True}
            {"fields": ["fek.date"], "unique": True}
        ],
    }

    instructionActKey = me.StringField(unique=True)
    instructionActType = me.StringField(
        required=True,
        choices=[
            "ΝΟΜΟΣ",
            "ΠΡΟΕΔΡΙΚΟ ΔΙΑΤΑΓΜΑ",
            "ΚΑΝΟΝΙΣΤΙΚΗ ΔΙΟΙΚΗΤΙΚΗ ΠΡΑΞΗ",
            "ΑΠΟΦΑΣΗ ΤΟΥ ΟΡΓΑΝΟΥ ΔΙΟΙΚΗΣΗΣ",
            "ΑΛΛΟ",
        ],
        unique_with=["instructionActTypeOther", "instructionActNumber", "instructionActDateOrYear"],
    )
    instructionActTypeOther = me.StringField(unique_with=["instructionActNumber", "instructionActDateOrYear"])
    instructionActNumber = me.StringField(required=True)
    instructionActDateOrYear = me.StringField(required=True)
    # fek = me.EmbeddedDocumentField(FEK, unique=True)
    fek = me.EmbeddedDocumentField(FEK)
    ada = me.StringField(default=default_ada, unique=True)
    instructionActFile = me.ReferenceField(FileUpload, required=True)

    @property
    def fek_info(self):
        # if not self.fek.number or not self.fek.issue or not self.fek.date:
        if not self.fek.date:    
            fek_number = f"ΜΗ ΔΗΜΟΣΙΕΥΤΕΑ ΟΔΗΓΙΑ-{uuid.uuid4()}"
            # self.fek.number = fek_number
            # self.fek.issue = ""
            self.fek.date = ""
            return fek_number
        else:
            fek_date = datetime.strptime(self.fek.date, "%Y-%m-%d")
            # return f"ΦΕΚ {self.fek.number}/{self.fek.issue}/{fek_date.strftime('%d-%m-%Y')}"
            return f"ΟΔΗΓΙΑ {fek_date.strftime('%d-%m-%Y')}"

    @property
    def instructionActTypeGeneral(self):
        return self.instructionActType if self.instructionActType != "ΑΛΛΟ" else self.instructionActTypeOther

    @property
    def fek_filename(self):
        return f"{self.instructionActTypeGeneral} {self.instructionActNumber}/{self.instructionActDateOrYear} {self.fek_info}"

    @property
    def key2str(self):
        if "ΜΗ ΔΗΜΟΣΙΕΥΤΕΑ ΠΡΑΞΗ" in self.fek_info:
            return f"{self.instructionActTypeGeneral} {self.instructionActNumber}/{self.instructionActDateOrYear} ΜΗ ΔΗΜΟΣΙΕΥΤΕΑ ΠΡΑΞΗ"
        else:
            return self.instructionActKey

    def create_key(self):
        if self.instructionActType == "ΑΛΛΟ":
            if not self.instructionActTypeOther:
                raise ValueError("Ο τύπος πράξης δεν μπορεί να είναι κενός ενώ επιλέξατε 'ΑΛΛΟ'")
            if self.instructionActTypeOther in [
                "ΝΟΜΟΣ",
                "ΠΡΟΕΔΡΙΚΟ ΔΙΑΤΑΓΜΑ",
                "ΚΑΝΟΝΙΣΤΙΚΗ ΔΙΟΙΚΗΤΙΚΗ ΠΡΑΞΗ",
                "ΑΠΟΦΑΣΗ ΤΟΥ ΟΡΓΑΝΟΥ ΔΙΟΙΚΗΣΗΣ",
                "ΑΛΛΟ",
            ]:
                raise ValueError(
                    "Ο τύπος πράξης δεν μπορεί να είναι κάποια από τις τιμές 'ΝΟΜΟΣ', 'ΠΡΟΕΔΡΙΚΟ ΔΙΑΤΑΓΜΑ', 'ΚΑΝΟΝΙΣΤΙΚΗ ΔΙΟΙΚΗΤΙΚΗ ΠΡΑΞΗ', 'ΑΠΟΦΑΣΗ ΤΟΥ ΟΡΓΑΝΟΥ ΔΙΟΙΚΗΣΗΣ', 'ΑΛΛΟ'"
                )
            return f"{self.instructionActTypeOther} {self.instructionActNumber}/{self.instructionActDateOrYear} {self.fek_info}"
        else:
            return f"{self.instructionActType} {self.instructionActNumber}/{self.instructionActDateOrYear} {self.fek_info}"

    def save(self, *args, **kwargs):
        instructionActKey = self.create_key()

        existingDoc = InstructionAct.objects(instructionActKey=instructionActKey).first()
        if existingDoc:
            raise ValueError(f"Υπάρχει ήδη νομική πράξη με κλειδί {instructionActKey}")

        self.instructionActKey = instructionActKey

        file = FileUpload.objects.get(id=ObjectId(self.instructionActFile.id))
        if not file:
            raise ValueError(f"Δεν βρέθηκε αρχείο με id {self.instructionActFile.file_id}")
        file.update(file_name=self.fek_filename)

        super(InstructionAct, self).save(*args, **kwargs)
