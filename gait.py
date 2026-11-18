"""Distance-driven two-joint gait in the student's local coordinate system."""
import math

STRIDE = .96
STANCE = .60
THIGH = .435
SHIN = .405
HIP = .895
ANKLE = .065


def foot_target(phase):
    half = STRIDE * STANCE / 2
    if phase < STANCE:
        forward = half - STRIDE * phase
        lift = pitch = 0
    else:
        u = (phase-STANCE)/(1-STANCE)
        forward = half * (2*u*u*(3-2*u)-1)
        lift = .09 * math.sin(math.pi*u)**2
        pitch = -16 * math.sin(math.tau*u)
    return forward, lift, pitch


def leg_pose(target, width, hip_height, weight):
    """Keep the sole still during stance and lift the foot during swing."""
    forward, lift, pitch = target
    forward = forward * weight / width
    vertical = hip_height - ANKLE - lift * weight
    reach = min(THIGH + SHIN - .001, math.hypot(forward, vertical))
    thigh = math.atan2(forward,vertical) + math.acos(
        (THIGH**2 + reach**2 - SHIN**2)/(2*THIGH*reach))
    knee = math.acos((reach**2-THIGH**2-SHIN**2)/(2*THIGH*SHIN))
    hip_angle = math.degrees(thigh)
    knee_angle = -math.degrees(knee)
    return hip_angle, knee_angle, pitch*weight-hip_angle-knee_angle


class StudentGait:
    def __init__(self, rig, torso, legs, shoulders, width):
        self.rig = rig
        self.torso = torso
        self.legs = legs
        self.shoulders = shoulders
        self.width = width
        self.distance = 0.
        self.weight = 0.

    def update(self, distance, dt):
        self.distance += distance
        target = 1 if distance > 0 else 0
        self.weight += (target-self.weight) * (1-math.exp(-11*dt))
        phase = self.distance / STRIDE
        cycles = (phase%1, (phase+.5)%1)
        targets = [foot_target(cycle) for cycle in cycles]
        furthest = max(abs(forward)*self.weight/self.width
                       for forward, _, _ in targets)
        reach = THIGH+SHIN-.006
        hip_height = min(HIP, ANKLE+math.sqrt(reach**2-furthest**2))
        self.rig.setZ((hip_height-HIP)*self.rig.getSz())
        self.torso.setH(3.8 * math.sin(math.tau*phase)*self.weight)
        for index, (hip,knee,ankle) in enumerate(self.legs):
            cycle = cycles[index]
            for joint, angle in zip((hip,knee,ankle),leg_pose(targets[index],self.width,hip_height,self.weight)):
                joint.setP(angle)
            self.shoulders[index].setP(-15*math.cos(math.tau*cycle)*self.weight)

    def reset(self):
        self.distance = self.weight = 0.
        self.update(0,0)
