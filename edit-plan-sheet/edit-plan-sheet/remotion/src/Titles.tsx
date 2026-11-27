import React from 'react';
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {outline, placement, textWrap} from './Captions';
import {StyleProps, TitleItem} from './types';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const TitleCard: React.FC<{t: TitleItem; style: StyleProps}> = ({t, style}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const unit = Math.min(width, height);
  const inn = interpolate(frame, [0, 10], [0, 1], clamp);
  const out = interpolate(frame, [t.dur - 8, t.dur], [1, 0], clamp);
  const opacity = Math.min(inn, out);
  const scale = 0.94 + 0.06 * inn;
  const fontSize = unit * 0.095;
  return (
    <AbsoluteFill style={{backgroundColor: t.dim ? `rgba(0,0,0,${(0.35 * opacity).toFixed(3)})` : 'transparent'}}>
      <div style={placement(t.position, width, height)}>
        <div
          lang={style.lang}
          style={{
            fontFamily: style.fontFamily,
            textAlign: 'center',
            maxWidth: width * 0.84,
            ...textWrap(style.lang),
            whiteSpace: 'pre-line',
            opacity,
            transform: `scale(${scale})`,
            willChange: 'transform',
          }}
        >
          <div
            style={{
              fontSize,
              fontWeight: style.fontWeight,
              lineHeight: 1.15,
              color: style.textColor,
              textShadow: outline(fontSize * 0.05, style.outlineColor),
            }}
          >
            {t.text}
          </div>
          {t.sub ? (
            <div
              style={{
                marginTop: fontSize * 0.3,
                fontSize: fontSize * 0.45,
                fontWeight: 600,
                color: style.accentColor,
                textShadow: outline(fontSize * 0.03, style.outlineColor),
              }}
            >
              {t.sub}
            </div>
          ) : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const LowerThird: React.FC<{t: TitleItem; style: StyleProps}> = ({t, style}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const unit = Math.min(width, height);
  const inn = interpolate(frame, [0, 10], [0, 1], clamp);
  const out = interpolate(frame, [t.dur - 8, t.dur], [1, 0], clamp);
  const fontSize = unit * 0.045;
  const vertical = height > width;
  const pos: React.CSSProperties =
    t.position === 'top' ? {top: height * (vertical ? 0.12 : 0.08)} : {bottom: height * (vertical ? 0.3 : 0.16)};
  return (
    <div
      lang={style.lang}
      style={{
        position: 'absolute',
        left: width * 0.06,
        ...pos,
        maxWidth: width * 0.8,
        display: 'flex',
        fontFamily: style.fontFamily,
        opacity: Math.min(inn, out),
        transform: `translateX(${((1 - inn) * -40).toFixed(2)}px)`,
        willChange: 'transform',
      }}
    >
      <div style={{width: fontSize * 0.22, backgroundColor: style.accentColor, borderRadius: 4}} />
      <div style={{backgroundColor: style.boxColor, padding: `${fontSize * 0.35}px ${fontSize * 0.6}px`}}>
        <div
          style={{fontSize, fontWeight: style.fontWeight, color: style.textColor, lineHeight: 1.2, ...textWrap(style.lang)}}
        >
          {t.text}
        </div>
        {t.sub ? (
          <div style={{fontSize: fontSize * 0.62, fontWeight: 500, color: style.textColor, opacity: 0.85, marginTop: fontSize * 0.15}}>
            {t.sub}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export const Titles: React.FC<{titles: TitleItem[]; style: StyleProps}> = ({titles, style}) => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    {titles.map((t, i) => (
      <Sequence key={`title-${i}`} from={t.from} durationInFrames={Math.max(1, t.dur)} name={`${t.kind} ${i + 1}`}>
        {t.kind === 'lower_third' ? <LowerThird t={t} style={style} /> : <TitleCard t={t} style={style} />}
      </Sequence>
    ))}
  </AbsoluteFill>
);
