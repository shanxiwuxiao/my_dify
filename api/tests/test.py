def demo():
    print("开始")
    yield "A"
    print("到中间了")
    yield "B"
    print("结束")
    yield "C"

def main():
    for d in demo():
        return
        

if __name__ == "__main__":
    main()
