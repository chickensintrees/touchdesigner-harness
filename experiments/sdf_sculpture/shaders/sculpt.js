// sdf_sculpture: liquid chrome. A breathing noisy core with two drops orbiting and melting into it.
// Compile: node <shader-park>/compile.mjs shaders/sculpt.js shaders  ->  shaders/sculpt.top.glsl
setMaxIterations(220);
setStepSize(0.55); // noise displacement overshoots the SDF; smaller steps remove edge streaks
let speed = input(0.5, 0.0, 2.0);
let t = time * speed;
let s = getSpace();
let n = noise(s * 2.6 + vec3(0, t, 0));

rotateY(t * 0.35);
rotateX(sin(t * 0.3) * 0.35);

// iridescent colour: phase-shifted sines driven by the surface noise
let ph = n * 5.0 + t;
let band = vec3(sin(ph), sin(ph + 2.1), sin(ph + 4.2));
color(band * band * 0.55);
metal(0.85);
shine(1.0);

sphere(0.5 + n * 0.1);

blend(0.18);
shape(() => {
  displace(sin(t * 1.1) * 0.72, cos(t * 0.8) * 0.3, sin(t * 0.6) * 0.2);
  sphere(0.17);
})();

blend(0.18);
shape(() => {
  displace(cos(t * 0.9) * -0.7, sin(t * 1.3) * 0.36, cos(t * 0.7) * 0.25);
  sphere(0.14);
})();
