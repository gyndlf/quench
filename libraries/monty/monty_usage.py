
from monty import Monty
import numpy as np


#%%
experiment = {
    "desc": "Sweeping the gates as i clean the floor",
    "meta": "This is a test file"
}

m = Monty("SET.ST_sweep", experiment)


m.newrun("initial_test", {
    "p1": "This is just a simple parameter for my experiment",
    "ST": "Sweeping from -1 to 333",
})

for i in range(0,10):
    data = np.random.rand(10)
    m.snapshot({
        "data": data,
        "ddot": "big bigger biggest (other data)"
    })

m.save({
    "data": data,
    "final": "final save",
    "ddot": "big bigger biggest"
})


#%%

m.newrun("another", {
    "p3": "This is just a simple parameter for my experiment",
    "STTTT": "Sweeping from -1 to 333",
})

m.save({
    "data": "some_final data goes here"
})


#m.savefig(plt)

#%%

m.loadexperiment("SET.ST_sweep")

m.loadrun("another")
