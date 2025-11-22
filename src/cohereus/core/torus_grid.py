"""
Torus Grid Topology — Edge-Free Cohort Manifold

Provides toroidal topology for cohort placement and neighbor diffusion.
Wrap-around boundaries ensure no edge effects, critical for national-scale
stability without artificial boundary conditions.

DNA Source: Topological concepts from EchoZero's distributed mesh patterns
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from typing import Tuple, Iterable, List


@dataclass
class TorusGrid:
    """
    2D torus grid for cohort placement and neighbor diffusion.

    Key properties:
    - Wrap-around boundaries (no edges)
    - Uniform neighbor topology
    - Distance preserving under wrapping
    - Enables phase diversity without boundary artifacts

    Example:
        grid = TorusGrid(width=4, height=3)  # 12 cohorts
        neighbors = grid.neighbors8(0, 0)
        distance = grid.torus_distance((0, 0), (3, 2))
    """

    width: int
    height: int

    def wrap(self, x: int, y: int) -> Tuple[int, int]:
        """
        Wrap coordinates onto torus (modulo arithmetic).

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Wrapped (x, y) coordinates
        """
        return x % self.width, y % self.height

    def index(self, x: int, y: int) -> int:
        """
        Convert 2D coordinates to linear index.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Linear index [0, width*height)
        """
        xw, yw = self.wrap(x, y)
        return yw * self.width + xw

    def coords(self, idx: int) -> Tuple[int, int]:
        """
        Convert linear index to 2D coordinates.

        Args:
            idx: Linear index

        Returns:
            (x, y) coordinates
        """
        y = idx // self.width
        x = idx % self.width
        return x, y

    def torus_distance(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """
        Shortest-path distance on a torus (geodesic).

        Critical for phase diversity calculations - ensures accurate
        neighbor distance even across wrapping boundaries.

        Args:
            a: First coordinate (x, y)
            b: Second coordinate (x, y)

        Returns:
            Euclidean distance on torus manifold
        """
        ax, ay = a
        bx, by = b

        # Minimum distance accounting for wrap-around
        dx = min(abs(ax - bx), self.width - abs(ax - bx))
        dy = min(abs(ay - by), self.height - abs(ay - by))

        return float(np.sqrt(dx*dx + dy*dy))

    def neighbors4(self, x: int, y: int) -> List[Tuple[int, int]]:
        """
        Von Neumann neighborhood (4-neighbors: up, down, left, right).

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            List of 4 neighbor coordinates
        """
        return [
            self.wrap(x + 1, y),
            self.wrap(x - 1, y),
            self.wrap(x, y + 1),
            self.wrap(x, y - 1),
        ]

    def neighbors8(self, x: int, y: int) -> List[Tuple[int, int]]:
        """
        Moore neighborhood (8-neighbors: all adjacent cells).

        Used for fracton density and phase coherence calculations.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            List of 8 neighbor coordinates
        """
        neigh = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                neigh.append(self.wrap(x + dx, y + dy))
        return neigh

    def ring_walk(self, start: Tuple[int, int], radius: int) -> Iterable[Tuple[int, int]]:
        """
        Iterator over coordinates at given torus radius (Manhattan ring).

        Useful for:
        - Diffusion shell scheduling
        - Rebalancing by concentric rings
        - Phase diversity enforcement

        Args:
            start: Starting coordinate
            radius: Manhattan distance radius

        Yields:
            Coordinates at specified radius
        """
        sx, sy = start
        r = radius

        # Top and bottom edges of ring
        for dx in range(-r, r + 1):
            yield self.wrap(sx + dx, sy - r)
            yield self.wrap(sx + dx, sy + r)

        # Left and right edges of ring
        for dy in range(-r + 1, r):
            yield self.wrap(sx - r, sy + dy)
            yield self.wrap(sx + r, sy + dy)

    @property
    def size(self) -> int:
        """Total number of grid cells (cohorts)."""
        return self.width * self.height


# Example usage and validation
if __name__ == "__main__":
    print("Testing Torus Grid...")

    # Create 4x3 grid (12 cohorts)
    grid = TorusGrid(width=4, height=3)

    print(f"\n1. Grid properties:")
    print(f"  Size: {grid.size} cohorts")
    print(f"  Dimensions: {grid.width}x{grid.height}")

    # Test wrapping
    print(f"\n2. Wrap-around test:")
    print(f"  wrap(4, 3) = {grid.wrap(4, 3)}")  # Should be (0, 0)
    print(f"  wrap(-1, -1) = {grid.wrap(-1, -1)}")  # Should be (3, 2)

    # Test distance
    print(f"\n3. Torus distance test:")
    dist1 = grid.torus_distance((0, 0), (3, 0))
    dist2 = grid.torus_distance((0, 0), (2, 0))
    print(f"  Distance (0,0) → (3,0): {dist1:.3f} (wraps to 1)")
    print(f"  Distance (0,0) → (2,0): {dist2:.3f}")

    # Test neighbors
    print(f"\n4. Neighbor test:")
    neigh4 = grid.neighbors4(0, 0)
    neigh8 = grid.neighbors8(0, 0)
    print(f"  4-neighbors of (0,0): {neigh4}")
    print(f"  8-neighbors of (0,0): {neigh8}")

    # Test ring walk
    print(f"\n5. Ring walk test:")
    ring0 = list(grid.ring_walk((1, 1), 0))
    ring1 = list(grid.ring_walk((1, 1), 1))
    print(f"  Ring r=0 from (1,1): {len(ring0)} cells")
    print(f"  Ring r=1 from (1,1): {len(set(ring1))} unique cells")

    print(f"\n✓ Torus Grid operational")
