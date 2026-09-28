/** Shared animation state, independent of the renderer and frame rate. */
export const DURATION = 6.875;
export const STATIC_TIME = 1;
export const CAMERA_FOV = 31;
export const ASSEMBLY_DEPTHS = { face: .4, feather: -.45, botanical: -.12, gems: 1.1 } as const;

const smooth = (value: number) => {
  const t = Math.max(0, Math.min(value, 1));
  return Math.max(0, Math.min(t * t * t * (t * (t * 6 - 15) + 10), 1));
};
const phase = (t: number, start: number, end: number) => smooth((t - start) / (end - start));
type Point3 = [number, number, number];

export function getPantherFrame(seconds: number, aspect = 1) {
  const remainder = seconds % DURATION;
  const time = remainder < 0 ? remainder + DURATION : remainder;
  // The final Form & finish return is brisker; the opening, scan and assembly
  // retain their approved pacing. Smooth easing still closes the loop.
  const pullback = phase(time, .4, 1) * (1 - phase(time, 6, DURATION));
  const technical = phase(time, 1, 2.2) * (1 - phase(time, 4.5, 6));
  const exploded = phase(time, 2.2, 3.1) * (1 - phase(time, 3.35, 4.5));
  const chapter = time < 1 || time >= 6
    ? '01|Form & finish'
    : time < 2.2 || time >= 4.5
      ? '02|Beneath the surface'
      : '03|The assembly';

  return {
    time,
    progress: time / DURATION,
    pullback,
    technical,
    exploded,
    sweep: 3.5 - 7 * technical,
    rotation: [.055 + .035 * exploded, -.12 - .22 * pullback - .30 * exploded, -.025 * pullback] as Point3,
    camera: [.1, .45 + .15 * pullback, (11.8 + 2.1 * pullback) / Math.min(aspect, 1)] as Point3,
    target: [0, .1 * (1 - pullback), 0] as Point3,
    chapter,
  };
}
