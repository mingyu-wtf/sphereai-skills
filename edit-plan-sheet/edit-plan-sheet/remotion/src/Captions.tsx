import React from 'react';
import {AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {CaptionItem, StyleProps} from './types';

type Segment = {text: string; hl: boolean};

// Splits text into plain and highlighted runs (case-insensitive, longest match first).
export const splitHighlights = (text: string, words: string[]): Segment[] => {
  const list = words.filter((w) => w && w.trim()).sort((a, b) => b.length - a.length);
  if (list.length === 0) return [{text, hl: false}];
  const lower = text.toLowerCase();
  const out: Segment[] = [];
  let i = 0;
  let plain = '';
  while (i < text.length) {
    const hit = list.find((w) => lower.startsWith(w.toLowerCase(), i));
    if (hit) {
      if (plain) out.push({text: plain, hl: false});
      plain = '';
      out.push({text: text.slice(i, i + hit.length), hl: true});
      i += hit.length;
    } else {
      plain += text[i];
      i += 1;
    }
  }
  if (plain) out.push({text: plain, hl: false});
  return out;
};

// Text outline built from shadows. Works with every font and script, unlike -webkit-text-stroke,
// which draws ugly inner lines on overlapping CJK strokes.
export const outline = (px: number, color: string): string => {
  const parts: string[] = [];
  const steps = 16;
  for (let s = 0; s < steps; s++) {
    const a = (s / steps) * Math.PI * 2;
    parts.push(`${(Math.cos(a) * px).toFixed(2)}px ${(Math.sin(a) * px).toFixed(2)}px 0 ${color}`);
  }
  parts.push(`0 ${(px * 0.9).toFixed(2)}px ${(px * 1.6).toFixed(2)}px rgba(0,0,0,0.6)`);
  return parts.join(', ');
};

// Korean: keep-all stops words breaking mid-word. Japanese/Chinese: normal CJK breaking plus
// strict line-break rules, so a line never starts with 、 or 。. Everything: never overflow the frame.
// text-wrap: balance evens out line lengths, so a wrapped caption does not leave one word alone.
export const textWrap = (lang: string): React.CSSProperties =>
  ({
    wordBreak: lang === 'ko' ? 'keep-all' : 'normal',
    overflowWrap: 'break-word',
    lineBreak: 'strict',
    textWrap: 'balance',
  }) as React.CSSProperties;

export const placement = (position: CaptionItem['position'], width: number, height: number): React.CSSProperties => {
  const vertical = height > width;
  const base: React.CSSProperties = {position: 'absolute', left: 0, right: 0, display: 'flex', justifyContent: 'center'};
  switch (position) {
    case 'top':
      return {...base, top: height * (vertical ? 0.14 : 0.08)};
    case 'center':
      return {...base, top: '50%', transform: 'translateY(-50%)'};
    case 'lower':
      return {...base, top: '68%', transform: 'translateY(-50%)'};
    case 'bottom':
    default:
      // Vertical videos keep clear of the app's bottom UI (title, buttons).
      return {...base, bottom: height * (vertical ? 0.17 : 0.07)};
  }
};

const Caption: React.FC<{c: CaptionItem; style: StyleProps}> = ({c, style}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const unit = Math.min(width, height);
  const segments = splitHighlights(c.text, c.highlight);
  const fadeOut = interpolate(frame, [c.dur - 3, c.dur], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const fadeIn = interpolate(frame, [0, 3], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const opacity = Math.min(fadeIn, fadeOut);
  const textBase: React.CSSProperties = {
    fontFamily: style.fontFamily,
    textAlign: 'center',
    whiteSpace: 'pre-line',
    ...textWrap(style.lang),
  };
  const runs = segments.map((s, i) => (
    <span key={i} style={s.hl ? {color: style.accentColor} : undefined}>
      {s.text}
    </span>
  ));

  if (c.style === 'shorts') {
    const fontSize = unit * 0.083 * style.captionScale;
    const pop = spring({frame, fps, durationInFrames: 8, config: {damping: 14, stiffness: 220}});
    const scale = 0.82 + 0.18 * pop;
    return (
      <div style={placement(c.position, width, height)}>
        <div
          lang={style.lang}
          style={{
            ...textBase,
            maxWidth: width * 0.82,
            fontSize,
            fontWeight: style.fontWeight,
            lineHeight: 1.2,
            color: style.textColor,
            textShadow: outline(fontSize * 0.075, style.outlineColor),
            transform: `scale(${scale})`,
            willChange: 'transform',
            opacity,
          }}
        >
          {runs}
        </div>
      </div>
    );
  }

  const fontSize = unit * 0.048 * style.captionScale;
  return (
    <div style={placement(c.position, width, height)}>
      <div lang={style.lang} style={{...textBase, maxWidth: width * 0.86, fontSize, fontWeight: 600, lineHeight: 1.45, opacity}}>
        <span
          style={{
            backgroundColor: style.boxColor,
            color: style.textColor,
            padding: '0.12em 0.45em',
            borderRadius: '0.18em',
            boxDecorationBreak: 'clone',
            WebkitBoxDecorationBreak: 'clone',
          }}
        >
          {runs}
        </span>
      </div>
    </div>
  );
};

export const Captions: React.FC<{captions: CaptionItem[]; style: StyleProps}> = ({captions, style}) => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    {captions.map((c, i) => (
      <Sequence key={`cap-${i}`} from={c.from} durationInFrames={Math.max(1, c.dur)} name={`caption ${i + 1}`}>
        <Caption c={c} style={style} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
