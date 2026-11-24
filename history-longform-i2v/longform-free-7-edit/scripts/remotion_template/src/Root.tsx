import React from "react";
import { Composition } from "remotion";
import { Episode, Timeline } from "./Episode";
import timeline from "./timeline.json";

const tl = timeline as unknown as Timeline;

export const Root: React.FC = () => (
  <Composition
    id="Episode"
    component={Episode}
    width={tl.width}
    height={tl.height}
    fps={tl.fps}
    durationInFrames={tl.totalFrames}
    defaultProps={{ timeline: tl }}
  />
);
