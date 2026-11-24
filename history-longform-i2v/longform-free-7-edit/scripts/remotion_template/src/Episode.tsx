import React from "react";
import { AbsoluteFill, Audio, Easing, Freeze, Img, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame } from "remotion";

export type Cut = { id: string; image?: string; clip?: string; clipSec?: number; from: number; frames: number; mode: number };
export type Cap = { from: number; frames: number; text: string };
export type Timeline = { width: number; height: number; fps: number; totalFrames: number; narration: string; bgm?: string; bgmVolume: number; cuts: Cut[]; captions: Cap[] };

const ease = Easing.inOut(Easing.cubic);

// 모드 0 줌인 / 1 줌아웃 / 2 왼→오 이동 / 3 오→왼 이동. 렌더러가 프레임마다 소수점 위치로 그려 떨리지 않는다.
const Mover: React.FC<{ frames: number; mode: number; frame: number; children: React.ReactNode }> = ({ frames, mode, frame, children }) => {
  const p = interpolate(frame, [0, Math.max(frames - 1, 1)], [0, 1], { easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  let scale = 1, tx = 0;
  if (mode === 0) scale = 1 + 0.1 * p;
  else if (mode === 1) scale = 1.1 - 0.1 * p;
  else if (mode === 2) { scale = 1.1; tx = (0.5 - p) * 4; }
  else { scale = 1.1; tx = (p - 0.5) * 4; }
  return <AbsoluteFill style={{ transform: `translateX(${tx}%) scale(${scale})`, transformOrigin: "50% 50%" }}>{children}</AbsoluteFill>;
};

const fit: React.CSSProperties = { width: "100%", height: "100%", objectFit: "cover" };

const ImageCut: React.FC<{ cut: Cut }> = ({ cut }) => {
  const frame = useCurrentFrame();
  return <Mover frames={cut.frames} mode={cut.mode} frame={frame}><Img src={staticFile(cut.image!)} style={fit} /></Mover>;
};

// 영상 클립: 컷이 클립보다 길면 최대 1.35배까지 느리게 늘리고, 남는 시간은 마지막 프레임을 천천히 확대한다. 영상은 자르지 않는다(컷이 더 짧으면 앞부분만 재생).
const ClipCut: React.FC<{ cut: Cut; fps: number }> = ({ cut, fps }) => {
  const frame = useCurrentFrame();
  const clipFrames = Math.round((cut.clipSec ?? 0) * fps);
  const stretch = clipFrames > 0 && cut.frames > clipFrames ? Math.min(cut.frames / clipFrames, 1.35) : 1;
  const playRate = 1 / stretch;
  const playFrames = Math.min(cut.frames, Math.round(clipFrames * stretch));
  const tailFrames = cut.frames - playFrames;
  return (
    <>
      <Sequence from={0} durationInFrames={Math.max(playFrames, 1)}>
        <OffthreadVideo src={staticFile(cut.clip!)} playbackRate={playRate} muted style={fit} />
      </Sequence>
      {tailFrames > 0 && (
        <Sequence from={playFrames} durationInFrames={tailFrames}>
          <Freeze frame={Math.max(clipFrames - 2, 0)}>
            <Mover frames={tailFrames} mode={0} frame={frame - playFrames}>
              <OffthreadVideo src={staticFile(cut.clip!)} muted style={fit} />
            </Mover>
          </Freeze>
        </Sequence>
      )}
    </>
  );
};

const Caption: React.FC<{ text: string }> = ({ text }) => (
  <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 70 }}>
    <div
      style={{
        fontFamily: '"Noto Sans KR","Malgun Gothic","Apple SD Gothic Neo","NanumGothic",sans-serif',
        fontWeight: 800, fontSize: 64, color: "#fff", textAlign: "center", maxWidth: "88%", lineHeight: 1.25,
        WebkitTextStroke: "10px #000", paintOrder: "stroke fill", whiteSpace: "nowrap",
      }}
    >{text}</div>
  </AbsoluteFill>
);

export const Episode: React.FC<{ timeline: Timeline }> = ({ timeline }) => (
  <AbsoluteFill style={{ backgroundColor: "#000" }}>
    {timeline.cuts.map((c) => (
      <Sequence key={c.id} from={c.from} durationInFrames={c.frames}>
        {c.clip ? <ClipCut cut={c} fps={timeline.fps} /> : <ImageCut cut={c} />}
      </Sequence>
    ))}
    {timeline.captions.map((c, i) => (
      <Sequence key={i} from={c.from} durationInFrames={c.frames}><Caption text={c.text} /></Sequence>
    ))}
    <Audio src={staticFile(timeline.narration)} />
    {timeline.bgm ? <Audio src={staticFile(timeline.bgm)} volume={timeline.bgmVolume} loop /> : null}
  </AbsoluteFill>
);
