try:
    import Queue as Q  # ver. < 3.0
except ImportError:
    import queue as Q

q = Q.PriorityQueue()
ti
q.put((10,"a"))
q.put((4,"b"))
q.put((1,"c"))
q.put((-11,"c"))
while not q.empty():
    print(q.get())