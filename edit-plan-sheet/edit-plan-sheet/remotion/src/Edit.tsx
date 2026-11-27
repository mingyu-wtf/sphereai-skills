import React, {useEffect, useState} from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  continueRender,
  delayRender,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {Captions} from './Captions';
import {Titles} from './Titles';
import {AudioItem, ClipItem, EditProps} from './types';

export const USER_FONT_FAMILY = 'EditUserFont';

// Loads the user's font file (style.font_file in edit.json) before any frame is captured.
const useUserFont = (fontUrl: string | null) => {
  const [handle] = useState(() => (fontUrl ? delayRender('Loading user font') : null));
  useEffect(() => {
    if (!fontUrl || handle === null) return;
    const face = new FontFace(USER_FONT_FAMILY, `url(${staticFile(fontUrl)})`);
    face
      .load()
      .then((f) => {
        // FontFaceSet.add exists in every browser; some TypeScript DOM typings omit it.
        (document.fonts as unknown as {add: (face: FontFace) => void}).add(f);
        return document.fonts.ready;
      })
      .then(() => continueRender(handle))
      .catch((err) => {
        console.error('Font failed to load, falling back to system fonts:', err);
        continueRender(handle);
      });
  }, [fontUrl, handle]);
};

const fill: React.CSSProperties = {width: '100%', height: '100%'};

// Original sound of a clip: base volume with short fades at the clip's edges (crossfades, click-free cuts).
const clipVolume = (clip: ClipItem, f: number): number => {
  let v = clip.volume;
  if (clip.audioFadeIn > 0) v *= Math.min(1, (f + 1) / clip.audioFadeIn);
  if (clip.audioFadeOut > 0) v *= Math.min(1, Math.max(0, (clip.dur - f) / clip.audioFadeOut));
  return Math.max(0, Math.min(1, v));
};

const Media: React.FC<{clip: ClipItem; objectFit: 'cover' | 'contain' | 'fill'; muted: boolean; extra?: React.CSSProperties}> = ({
  clip,
  objectFit,
  muted,
  extra,
}) => {
  const style: React.CSSProperties = {...fill, objectFit, ...extra};
  if (clip.kind === 'color' || !clip.src) {
    return <div style={{...fill, backgroundColor: clip.color, ...extra}} />;
  }
  if (clip.kind === 'image') {
    return <Img src={staticFile(clip.src)} style={style} />;
  }
  const silent = muted || clip.volume <= 0;
  return (
    <OffthreadVideo
      src={staticFile(clip.src)}
      trimBefore={clip.trimBefore > 0 ? clip.trimBefore : undefined}
      playbackRate={clip.speed}
      volume={silent ? 0 : (f: number) => clipVolume(clip, f)}
      muted={silent}
      style={style}
    />
  );
};

const hasCrop = (clip: ClipItem) =>
  clip.crop !== null &&
  clip.srcWidth > 0 &&
  clip.srcHeight > 0 &&
  clip.crop.top + clip.crop.bottom + clip.crop.left + clip.crop.right > 0;

// Shows only the kept part of the source (clip.crop), fitted into the frame like cover/contain.
// The full picture is drawn larger than its box and shifted so the cut-away edges fall outside it.
const CroppedMedia: React.FC<{clip: ClipItem; mode: 'cover' | 'contain'; muted: boolean; extra?: React.CSSProperties}> = ({
  clip,
  mode,
  muted,
  extra,
}) => {
  const {width, height} = useVideoConfig();
  const c = clip.crop!;
  const keepW = Math.max(0.05, 1 - c.left - c.right);
  const keepH = Math.max(0.05, 1 - c.top - c.bottom);
  const cw = clip.srcWidth * keepW;
  const ch = clip.srcHeight * keepH;
  const k = mode === 'cover' ? Math.max(width / cw, height / ch) : Math.min(width / cw, height / ch);
  const bw = cw * k;
  const bh = ch * k;
  const fullW = bw / keepW;
  const fullH = bh / keepH;
  return (
    <div style={{position: 'absolute', left: (width - bw) / 2, top: (height - bh) / 2, width: bw, height: bh, overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: -c.left * fullW, top: -c.top * fullH, width: fullW, height: fullH}}>
        <Media clip={clip} objectFit="fill" muted={muted} extra={extra} />
      </div>
    </div>
  );
};

const ClipLayer: React.FC<{clip: ClipItem}> = ({clip}) => {
  const frame = useCurrentFrame();
  const opacity =
    clip.fadeIn > 0 ? interpolate(frame, [0, clip.fadeIn], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 1;
  const t = clip.dur > 1 ? Math.min(1, Math.max(0, frame / (clip.dur - 1))) : 0;
  const scale = clip.zoom === 'in' ? 1 + clip.zoomAmount * t : clip.zoom === 'out' ? 1 + clip.zoomAmount * (1 - t) : 1;
  const objectFit = clip.fit === 'cover' ? 'cover' : 'contain';
  const cropped = hasCrop(clip);
  const blurStyle = {filter: 'blur(40px) brightness(0.55)'};
  return (
    <AbsoluteFill style={{opacity, overflow: 'hidden'}}>
      {clip.fit === 'blur' ? (
        // A blurred, enlarged copy fills the empty bars around a "contain" picture.
        <AbsoluteFill style={{transform: 'scale(1.15)'}}>
          {cropped ? (
            <CroppedMedia clip={clip} mode="cover" muted extra={blurStyle} />
          ) : (
            <Media clip={clip} objectFit="cover" muted extra={blurStyle} />
          )}
        </AbsoluteFill>
      ) : null}
      {/* will-change keeps the slow zoom on the GPU so edges and text do not shimmer. */}
      <AbsoluteFill style={{transform: `scale(${scale})`, willChange: 'transform'}}>
        {cropped ? (
          <CroppedMedia clip={clip} mode={objectFit} muted={false} />
        ) : (
          <Media clip={clip} objectFit={objectFit} muted={false} />
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Volume at a frame inside the audio's Sequence: base volume, fades, then ducking under narration.
const envelope = (item: AudioItem, localFrame: number): number => {
  let v = item.volume;
  if (item.fadeIn > 0) v *= Math.min(1, localFrame / item.fadeIn);
  if (item.fadeOut > 0) v *= Math.min(1, Math.max(0, (item.dur - localFrame) / item.fadeOut));
  if (item.duck.length > 0) {
    const abs = item.from + localFrame;
    const r = Math.max(1, item.duckRamp);
    let g = 1;
    for (const [a, b] of item.duck) {
      let k: number;
      if (abs >= a && abs <= b) k = 0;
      else if (abs > a - r && abs < a) k = (a - abs) / r;
      else if (abs > b && abs < b + r) k = (abs - b) / r;
      else continue;
      g = Math.min(g, item.duckFactor + (1 - item.duckFactor) * k);
    }
    v *= g;
  }
  return Math.max(0, Math.min(1, v));
};

export const Edit: React.FC<EditProps> = (props) => {
  useUserFont(props.style.fontUrl);
  return (
    <AbsoluteFill style={{backgroundColor: props.background}}>
      {props.clips.map((clip, i) => (
        <Sequence key={`clip-${i}`} from={clip.from} durationInFrames={Math.max(1, clip.dur)} name={`clip ${i + 1}`}>
          <ClipLayer clip={clip} />
        </Sequence>
      ))}
      {props.audio.map((a, i) => (
        <Sequence key={`audio-${i}`} from={a.from} durationInFrames={Math.max(1, a.dur)} name={`audio ${i + 1}`} layout="none">
          <Audio
            src={staticFile(a.src)}
            trimBefore={a.trimBefore > 0 ? a.trimBefore : undefined}
            loop={a.loop}
            volume={(f) => envelope(a, f)}
          />
        </Sequence>
      ))}
      <Titles titles={props.titles} style={props.style} />
      <Captions captions={props.captions} style={props.style} />
    </AbsoluteFill>
  );
};
