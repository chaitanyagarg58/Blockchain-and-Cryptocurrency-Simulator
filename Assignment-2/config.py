

class Config:
    remove_eclipse = False
    counter_measure = False

    @staticmethod
    def log(folder_to_store: str):
        with open(f"{folder_to_store}/config.txt", "w") as f:
            f.write(f"Remove Eclipse Attack -> {Config.remove_eclipse}\n")
            f.write(f"Counter Measure -> {Config.counter_measure}\n")