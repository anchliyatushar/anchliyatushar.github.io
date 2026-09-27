import { useState, type CSSProperties, type PointerEvent } from 'react';
import '../styles/cad-viewport.css';

type CadStyle = CSSProperties & Record<'--mouse-x' | '--mouse-y', string>;

export default function CadViewport() {
  const [rotation, setRotation] = useState({ x: 0, y: 0 });

  const handlePointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    setRotation({
      x: Number((((event.clientX - bounds.left) / bounds.width - 0.5) * 12).toFixed(2)),
      y: Number((-((event.clientY - bounds.top) / bounds.height - 0.5) * 10).toFixed(2)),
    });
  };

  const style = {
    '--mouse-x': `${rotation.x}deg`,
    '--mouse-y': `${rotation.y}deg`,
  } as CadStyle;

  return (
    <div
      className="cad-scene group relative aspect-square w-full max-w-[43rem] overflow-hidden rounded-md border border-cyan-100/20 bg-[#080b0c] shadow-[inset_0_0_100px_rgba(0,0,0,.4),0_20px_80px_rgba(0,0,0,.3)]"
      data-cad-scene
      onPointerMove={handlePointerMove}
      onPointerLeave={() => setRotation({ x: 0, y: 0 })}
      style={style}
      aria-label="Interactive 3D CAD ring model"
      role="img"
    >
      <div className="cad-floor" />
      <div className="cad-backplane" />
      <div className="cad-axes cad-axes-x"><span>X</span></div>
      <div className="cad-axes cad-axes-y"><span>Y</span></div>
      <div className="cad-axes cad-axes-z"><span>Z</span></div>
      <div className="cad-float absolute inset-[8%]">
        <div className="cad-rotation h-full w-full">
          <svg className="cad-model h-full w-full overflow-visible" viewBox="0 0 600 600" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <defs>
              <linearGradient id="goldSurface" x1="152" y1="82" x2="454" y2="506" gradientUnits="userSpaceOnUse"><stop stopColor="#FFF4C6"/><stop offset=".18" stopColor="#E8C25A"/><stop offset=".5" stopColor="#9B6818"/><stop offset=".77" stopColor="#F2D273"/><stop offset="1" stopColor="#714208"/></linearGradient>
              <linearGradient id="goldLine" x1="111" y1="240" x2="500" y2="370" gradientUnits="userSpaceOnUse"><stop stopColor="#805011"/><stop offset=".45" stopColor="#FFE38D"/><stop offset="1" stopColor="#9C6619"/></linearGradient>
              <radialGradient id="stone" cx="0" cy="0" r="1" gradientTransform="translate(301 226) rotate(90) scale(69)"><stop stopColor="#FFFCEC"/><stop offset=".28" stopColor="#D7E9F1"/><stop offset=".65" stopColor="#769BAC"/><stop offset="1" stopColor="#1A3443"/></radialGradient>
              <filter id="glow" x="78" y="52" width="444" height="483" filterUnits="userSpaceOnUse"><feGaussianBlur stdDeviation="8" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
            </defs>
            <g className="construction" opacity=".55"><ellipse cx="300" cy="302" rx="227" ry="89" stroke="#D9E6EA" strokeWidth="1.2" strokeDasharray="5 8"/><ellipse cx="300" cy="302" rx="159" ry="215" stroke="#D9E6EA" strokeWidth="1.2" strokeDasharray="5 8"/><path d="M50 302H550M300 58V544" stroke="#D9E6EA" strokeWidth="1.2" strokeDasharray="5 8"/><path d="M107 166L493 438M107 438L493 166" stroke="#D9E6EA" strokeWidth=".8" strokeDasharray="3 10"/></g>
            <g className="ring-body" filter="url(#glow)"><ellipse cx="300" cy="354" rx="144" ry="137" stroke="url(#goldSurface)" strokeWidth="34"/><ellipse cx="300" cy="354" rx="144" ry="137" stroke="url(#goldLine)" strokeWidth="3" opacity=".9"/><path d="M166 360C191 408 242 440 300 440C358 440 409 408 434 360" stroke="#FFEBA5" strokeWidth="2" opacity=".72"/><path d="M168 334C189 281 236 266 300 266C364 266 411 281 432 334" stroke="#76450A" strokeWidth="4" opacity=".86"/></g>
            <g className="crown"><path d="M213 255L235 161L273 194L300 132L327 194L365 161L387 255" fill="url(#goldSurface)" stroke="#FCE191" strokeWidth="2"/><path d="M213 255H387L356 307H244L213 255Z" fill="#9C6619" stroke="#F9DA7B" strokeWidth="2"/><path d="M244 307H356L331 333H269L244 307Z" fill="#744608"/><circle cx="300" cy="228" r="67" fill="url(#stone)" stroke="#FFF1B7" strokeWidth="8"/><path d="M254 182L300 228L346 182M238 228H362M254 274L300 228L346 274" stroke="#FFFFFF" strokeWidth="1.5" opacity=".82"/><circle cx="300" cy="228" r="16" fill="#FFFDF4" opacity=".9"/><g fill="#F8D36D" stroke="#805011" strokeWidth="2"><circle cx="221" cy="227" r="12"/><circle cx="247" cy="160" r="12"/><circle cx="300" cy="139" r="12"/><circle cx="353" cy="160" r="12"/><circle cx="379" cy="227" r="12"/></g></g>
            <g className="cad-dimensions" stroke="#B8E6FA" strokeWidth="1.3" opacity=".95"><path d="M137 465V514H463V465M137 495H463"/><path d="M137 495L148 489M137 495L148 501M463 495L452 489M463 495L452 501"/><path d="M453 176H498V343H453M478 176V343"/><path d="M478 176L472 187M478 176L484 187M478 343L472 332M478 343L484 332"/></g>
            <g className="cad-labels" fill="#E2F3FA"><text x="264" y="538">Ø 18.2 mm</text><text x="487" y="262" transform="rotate(90 487 262)">6.4 mm</text><text x="75" y="98">CONCEPT_RING</text><text x="75" y="116">VIEWPORT / 01</text></g>
          </svg>
        </div>
      </div>
      <span className="view-label view-label-top">Perspective</span><span className="view-label view-label-bottom">Drag to rotate</span>
    </div>
  );
}
