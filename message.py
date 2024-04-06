class Message:
	def __init__(self, Name: str, Lat: float, Log: float, Extra: str):
		self.Name = [*Name] + ["\0" for i in range(128-len(Name))]
		self.Name = [char.encode("utf-8") for char in self.Name]
		self.Lat = Lat
		self.Log = Log
		self.Extra = [*Extra]
		self.Extra = [char.encode("utf-8") for char in self.Extra]
