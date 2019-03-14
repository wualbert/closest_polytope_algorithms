# -*- coding: utf-8 -*-
'''

@author: wualbert
'''
import numpy as np
from gurobipy import Model, GRB
from pypolycontain.lib.zonotope import zonotope
from pypolycontain.lib.polytope import polytope
from pypolycontain.lib.inclusion_encodings import constraints_AB_eq_CD

class AABB:
    def __init__(self, vertices):
        '''
        Creates an axis-aligned bounding boxsort from two diagonal vertices
        :param vertices: a list of defining vertices with shape (2, dimensions)
        '''
        try:
            assert(len(vertices[0]) == len(vertices[1]))
        except AssertionError:
            print('Mismatched vertex dimensions')
            return
        self.dimension = len(vertices[0])
        self.u = np.asarray(vertices[0])
        self.v = np.asarray(vertices[1])

        for d in range(self.dimension):
            if vertices[0][d]>vertices[1][d]:
                self.v[d], self.u[d] = vertices[0][d], vertices[1][d]

    def __repr__(self):
        return "R^%d AABB with vertices "%(self.dimension) + np.array2string(self.u) +\
               ","+np.array2string(self.v)

    def overlaps(self, b2):
        '''
        U: lower corner. V: upper corner
        :param b2: boxsort to compare to
        :return:
        '''
        u1_leq_v2 = np.less_equal(self.u,b2.v)
        u2_leq_v1 = np.less_equal(b2.u, self.v)
        return u1_leq_v2.all() and u2_leq_v1.all()


def overlaps(a,b):
    return a.overlaps(b)

def point_to_box_distance(point, box):
    out_range_dim = []
    for dim in range(box.dimension):
        if box.u[dim] < point[dim] and box.v[dim] > point[dim]:
            pass
        else:
            out_range_dim.append(min(abs(box.u[dim]-point[dim]), abs(box.v[dim]-point[dim])))
    return np.linalg.norm(out_range_dim)


def box_to_box_distance(query_box, box):
    out_range_dim = []
    for dim in range(box.dimension):
        if (box.u[dim] < query_box.u[dim] and box.v[dim] > query_box.u[dim]) or \
            (box.u[dim] < query_box.v[dim] and box.v[dim] > query_box.v[dim]) or \
            (query_box.u[dim] < box.u[dim] and query_box.v[dim] > box.u[dim]) or \
            (query_box.u[dim] < box.v[dim] and query_box.v[dim] > box.v[dim]):
            pass
        else:
            out_range_dim.append(min(min(abs(box.u[dim]-query_box.u[dim]), abs(box.v[dim]-query_box.u[dim])),
                                 min(abs(box.u[dim]-query_box.v[dim]), abs(box.v[dim]-query_box.v[dim]))))
    return np.linalg.norm(out_range_dim)

def zonotope_to_box(z):
    model = Model("zonotope_AABB")

    dim=z.x.shape[0]
    p=np.empty((z.G.shape[1],1),dtype='object')
    #find extremum on each dimension
    results = [np.empty(z.x.shape[0]), np.empty(z.x.shape[0])]
    x = np.empty((z.x.shape[0],1),dtype='object')
    for row in range(p.shape[0]):
        p[row,0]=model.addVar(lb=-1,ub=1)
    model.update()
    for d in range(dim):
        x[d] = model.addVar(obj=0)
    constraints_AB_eq_CD(model,np.eye(dim),x-z.x,z.G,p)

    for d in range(dim):
        print(d)
        x[d,0].Obj = 1
        #find minimum
        model.ModelSense = 1
        model.update()
        model.optimize()
        assert(model.Status==2)
        results[0][d] = x[d,0].X
        print(results)
        #find maximum
        model.ModelSense = -1
        model.update()
        model.optimize()
        assert(model.Status==2)
        results[1][d] = x[d,0].X
        #reset coefficient
        x[d,0].obj = 0
        print(results)
    return AABB(results)