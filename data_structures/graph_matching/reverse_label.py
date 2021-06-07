

class ReverseLabel:

    labels = {}

    def __new__(cls, label):
        if isinstance(label, ReverseLabel):
            return label.label
        elif label in ReverseLabel.labels:
            return ReverseLabel.labels[label]
        else:
            rlabel = super(ReverseLabel, cls).__new__(cls)
            rlabel.__init__(label)
            ReverseLabel.labels[label] = rlabel
            return rlabel

    def __init__(self, label):
        self.label = label

    def __str__(self):
        return f'REV<{str(self.label)}>'

    def __repr__(self):
        return str(self)