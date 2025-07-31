from process import Process
import time

def main():
    process1 = Process(1, 5001, [5002, 5003])
    process2 = Process(2, 5002, [5001, 5003])
    process3 = Process(3, 5003, [5001, 5002])

    process1.start()
    process2.start()
    process3.start()

    time.sleep(10)
    process1.initiate_snapshot()

    time.sleep(10)
    process1.running = False
    process2.running = False
    process3.running = False

if __name__ == "__main__":
    main()
