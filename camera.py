#!/usr/bin/env python3
"""
camera.py - Source 2 3D Camera, ViewMatrix & WorldToScreen Projection

Implements pure Cartesian 3D linear algebra matching Source 2 client.dll:
  - Vector3 operations (dot, length, normalize)
  - Euler angle orientation (pitch, yaw, roll)
  - 4x4 ViewMatrix and Perspective Projection Matrix
  - 3D to 2D screen coordinate transformations
"""

import math
from typing import List, Tuple, Optional


class Vector3:
    __slots__ = ("x", "y", "z")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, o: "Vector3") -> "Vector3":
        return Vector3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o: "Vector3") -> "Vector3":
        return Vector3(self.x - o.x, self.y - o.y, self.z - o.z)

    def __mul__(self, s: float) -> "Vector3":
        return Vector3(self.x * s, self.y * s, self.z * s)

    def dot(self, o: "Vector3") -> float:
        return self.x * o.x + self.y * o.y + self.z * o.z

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self) -> "Vector3":
        l = self.length()
        return Vector3(self.x / l, self.y / l, self.z / l) if l > 1e-6 else Vector3(0, 0, 0)


def angle_vectors(pitch_deg: float, yaw_deg: float, roll_deg: float = 0.0) -> Tuple[Vector3, Vector3, Vector3]:
    """Computes forward, right, and up unit vectors from Euler rotation angles."""
    p = math.radians(pitch_deg)
    y = math.radians(yaw_deg)
    r = math.radians(roll_deg)

    sp, cp = math.sin(p), math.cos(p)
    sy, cy = math.sin(y), math.cos(y)
    sr, cr = math.sin(r), math.cos(r)

    forward = Vector3(cp * cy, cp * sy, -sp)
    right = Vector3(-1.0 * sr * sp * cy + -1.0 * cr * -sy,
                    -1.0 * sr * sp * sy + -1.0 * cr * cy,
                    -1.0 * sr * cp)
    up = Vector3(cr * sp * cy + -sr * -sy,
                 cr * sp * sy + -sr * cy,
                 cr * cp)
    return forward, right, up


def build_view_proj_matrix(cam_pos: Vector3,
                           forward: Vector3,
                           right: Vector3,
                           up: Vector3,
                           fov_deg: float = 90.0,
                           aspect_ratio: float = 16.0 / 9.0,
                           z_near: float = 7.0,
                           z_far: float = 28400.0) -> List[List[float]]:
    """Builds combined View-Projection 4x4 Matrix matching Source 2 client.dll."""
    view = [
        [right.x, right.y, right.z, -right.dot(cam_pos)],
        [up.x, up.y, up.z, -up.dot(cam_pos)],
        [-forward.x, -forward.y, -forward.z, forward.dot(cam_pos)],
        [0.0, 0.0, 0.0, 1.0]
    ]

    fov_rad = math.radians(fov_deg)
    tan_half_fov = math.tan(fov_rad / 2.0)
    proj = [[0.0] * 4 for _ in range(4)]
    proj[0][0] = 1.0 / (aspect_ratio * tan_half_fov)
    proj[1][1] = 1.0 / tan_half_fov
    proj[2][2] = -(z_far + z_near) / (z_far - z_near)
    proj[2][3] = -(2.0 * z_far * z_near) / (z_far - z_near)
    proj[3][2] = -1.0

    res = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            for k in range(4):
                res[i][j] += proj[i][k] * view[k][j]
    return res


def world_to_screen(world_pos: Vector3,
                    view_proj: List[List[float]],
                    screen_w: int,
                    screen_h: int) -> Optional[Tuple[float, float, float]]:
    """Transforms 3D Cartesian coordinates to 2D screen coordinates."""
    x = view_proj[0][0] * world_pos.x + view_proj[0][1] * world_pos.y + view_proj[0][2] * world_pos.z + view_proj[0][3]
    y = view_proj[1][0] * world_pos.x + view_proj[1][1] * world_pos.y + view_proj[1][2] * world_pos.z + view_proj[1][3]
    w = view_proj[3][0] * world_pos.x + view_proj[3][1] * world_pos.y + view_proj[3][2] * world_pos.z + view_proj[3][3]

    if w < 0.01:
        return None  # Point is behind camera frustum

    ndc_x = x / w
    ndc_y = y / w

    screen_x = (ndc_x + 1.0) * 0.5 * screen_w
    screen_y = (1.0 - ndc_y) * 0.5 * screen_h
    return screen_x, screen_y, w
