class Structure():

    def __init__(self, height: int | float, lat: float, long: float, period: float, vs30:float) -> None:
    #should implement the method for calculating natural period
        self.height = height
        self.latitude = lat
        self.longitude = long
        self.period = period
        self.vs30 = vs30

    def ground(self) -> "Structure":
        return Structure(height=self.height,
                         lat = self.latitude,
                         long = self.longitude,
                         period=0)

