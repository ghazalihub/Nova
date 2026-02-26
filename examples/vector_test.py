from src.nova.stdlib import Tensor
def vector_test():
    a = Tensor.randn([10])
    b = Tensor.randn([10])
    c = 5
    result = Tensor.randn([10])
    result = (a + (b * c))
    print("Vectorized loop result:")
    print(result)
vector_test()