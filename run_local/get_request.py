import main


class Request:
    method = "GET"


main.receiver(Request())
# will get an OutOfContext error but that is nothing to worry about
