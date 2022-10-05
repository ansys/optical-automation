def main():
    try:
        argsDict
        mode = 1
    except Exception:
        mode = 0

    if mode == 1:
        camera_model = argsDict["camera_model"]
        car_model = argsDict["car_model"]
        print(car_model + camera_model)
    elif mode == 0:
        pass


main()
