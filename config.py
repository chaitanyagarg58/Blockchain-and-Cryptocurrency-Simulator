

class Config:
    remove_eclipse = False
    counter_measure = False

    def log(folder_to_store: str):
        with open(f"{folder_to_store}/config.txt", "w") as f:
            f.writelines(f"Remove Eclipse Attack -> {Config.remove_eclipse}\n")
            f.writelines(f"Counter Measure -> {Config.counter_measure}\n")