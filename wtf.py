from fractions import Fraction
import math

class SturmRationalDebugger:
    def __init__(self, uR, balls, threshold=0):
        self.uR = Fraction(uR)
        self.r2 = self.uR * self.uR
        self.invR2 = Fraction(1, self.r2)
        self.balls = balls 
        self.THRESHOLD = Fraction(threshold)

    def poly_neg_remainder(self, A, B):
        """Returns -rem(A, B) using rational long division."""
        rem = list(A)
        while len(rem) >= len(B) and len(B) > 0:
            degree_diff = len(rem) - len(B)
            factor = rem[-1] / B[-1]
            for i in range(len(B)):
                rem[i + degree_diff] -= factor * B[i]
            # Clean precision zeros
            while len(rem) > 0 and rem[-1] == 0:
                rem.pop()
        return [-coeff for coeff in rem]

    def evaluate_poly(self, poly, x):
        val = Fraction(0)
        for i, coeff in enumerate(poly):
            val += coeff * (Fraction(x)**i)
        return val

    def count_sign_changes(self, sequence, x):
        # We evaluate each polynomial in the sequence at x
        vals = [self.evaluate_poly(p, x) for p in sequence]
        # Sturm theory: ignore zeros in the sequence for sign counting
        signs = [1 if v > 0 else -1 for v in vals if v != 0]
        
        changes = 0
        for i in range(len(signs) - 1):
            if signs[i] * signs[i+1] < 0:
                changes += 1
        return changes, vals
def rational_sqrt(frac):
    """
    Computes the square root of a Fraction. 
    Returns a Fraction if it's a perfect square, 
    otherwise falls back to a float-based Fraction.
    """
    # Ensure we are working with a Fraction
    f = Fraction(frac)
    
    if f < 0:
        raise ValueError("Cannot compute square root of a negative number.")
    if f == 0:
        return Fraction(0)

    p = f.numerator
    q = f.denominator

    # Compute integer square roots
    sqrt_p = math.isqrt(p)
    sqrt_q = math.isqrt(q)

    # Check if they are perfect squares
    is_p_perfect = (sqrt_p * sqrt_p == p)
    is_q_perfect = (sqrt_q * sqrt_q == q)

    if is_p_perfect and is_q_perfect:
        # Return the exact Fraction
        return Fraction(sqrt_p, sqrt_q)
    else:
        # Fallback: Compute float sqrt and convert back to Fraction
        # Note: We use str(float) to avoid binary float approximation artifacts
        res_float = math.sqrt(float(f))
        return Fraction(str(res_float))

def check(the_x):
    # Parameters from your JS example
    R = Fraction(45,100)
    uBalls = [{'x': 0, 'y': 0, 'z': 0}]
    threshold = Fraction(1,2);
    cam_pos = {'x': 0, 'y': 0, 'z': -2}
    world_pos = {'x': the_x, 'y': 0, 'z': 0}

    debugger = SturmRationalDebugger(R, uBalls, threshold)
    
    # 1. Calculate Ray Direction (Rationalized)
    dx = Fraction(world_pos['x']) - Fraction(cam_pos['x'])
    dy = Fraction(world_pos['y']) - Fraction(cam_pos['y'])
    dz = Fraction(world_pos['z']) - Fraction(cam_pos['z'])

    # print(f"dx = {dx} dy = {dy} dz = {dz}")
    
    # Calculate magnitude (we use math.sqrt then convert to Fraction for the 'rd')
    # Note: If this mag isn't exact, it's a source of drift, but Fraction(str(float)) 
    # is much more precise than a standard 32-bit float.
    mag_sq = dx**2 + dy**2 + dz**2
    mag = rational_sqrt(mag_sq)
    rd = {'x': dx/mag, 'y': dy/mag, 'z': dz/mag}
    ro = {k: Fraction(v) for k, v in cam_pos.items()}
    print(f"mag_sq = {mag_sq} mag = {mag} rd={rd} ro={ro}")

    # 2. Setup the Polynomial (Logic from your GLSL/JS)
    # We test t0 = 0 (the start of the ray effectively)

    e = [Fraction(0)] * 7
    r2 = R*R
    ball = uBalls[0]

    oc = {'x': Fraction(ball['x']) - ro['x'], 
          'y': Fraction(ball['y']) - ro['y'], 
          'z': Fraction(ball['z']) - ro['z']}
    
    b_val = oc['x']*rd['x'] + oc['y']*rd['y'] + oc['z']*rd['z']
    oc_dot_oc = oc['x']**2 + oc['y']**2 + oc['z']**2
    the_e2 = oc_dot_oc - b_val * b_val
    disc = r2 - the_e2  
    if disc < 0:
        return False
    print(f"disc = {disc}")
    sq = rational_sqrt(disc)
    print(f"sq = {sq}")
    tStart = b_val - sq
    tEnd = b_val + sq
    t0 = Fraction(tStart)

    print(f"t0 = {t0}")
    
    a2 = -debugger.invR2
    a1 = Fraction(2) * b_val * debugger.invR2
    a0 = Fraction(1) - oc_dot_oc * debugger.invR2

    c0 = t0*t0*a2 + t0*a1 + a0
    c1 = (t0*a2 * 2 + a1) * 2 * debugger.uR
    c2 = Fraction(-4)

    print(f"oc={oc} b_val={b_val} oc_dot_oc={oc_dot_oc}")
    print(f"a0={a0} a1={a1} a2={a2}")
    print(f"c0={c0} c1={c1} c2={c2}")


    e[6] += c2**3
    e[5] += 3 * c2**2 * c1
    e[4] += 3 * c2 * (c2*c0 + c1**2)
    e[3] += c1 * (6*c2*c0 + c1**2)
    e[2] += 3 * c0 * (c2*c0 + c1**2)
    e[1] += 3 * c1 * c0**2
    e[0] += c0**3

    # print(f"e = {e}")

    e[0] -= debugger.THRESHOLD

    # 3. Build Sequence
    P = [e]
    p1 = [e[i] * i for i in range(1, 7)]
    P.append(p1)

    while len(P[-1]) > 1:
        next_p = debugger.poly_neg_remainder(P[-2], P[-1])
        if not any(next_p): break
        P.append(next_p)

    for (i,p) in enumerate(P):
        z=[float(f) for f in p ]
        m=max([abs(v) for v in z])
        s=[v/m for v in z]
        print(f"p[{i}] = {s}")

    # 4. Check Interval [0, 1] (or any interval you suspect)
    check_points = [0, 1]
    # for x in check_points:
    #     changes, vals = debugger.count_sign_changes(P, x)
    #     print(f"--- Evaluation at x = {x} ---")
    #     print(f"Sign Changes: {changes}")
    #     for i, v in enumerate(vals):
    #         print(f"  P{i}({x}) = {float(v)}") # float for readability
    #     print()
    return debugger.count_sign_changes(P, 0)[0] > debugger.count_sign_changes(P, 1)[0]

def main():
    # check(Fraction(23,100));
    check(Fraction(45,100));
    return
    last=False
    for i in range(-100,100):
        x=Fraction(i,100)
        now=check(x)
        if now != last:
            print(f"{now} at {x}")
            last = now

if __name__ == "__main__":
    main()