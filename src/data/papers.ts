// Loads the research sections: the manifest (sections.yaml) defines order and
// titles; each sections/*.yaml file holds that section's papers in display
// order. Editing a YAML file and rebuilding is the whole workflow.
import { parse } from 'yaml';
import manifestRaw from './sections.yaml?raw';

const sectionFiles = import.meta.glob('./sections/*.yaml', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

export interface Link {
  text: string;
  url: string;
}

export interface Stat {
  value: string;
  label: string;
}

// Homepage highlight: the first paper with `feature` in an on_homepage section.
export interface Feature {
  kicker: string;
  meta?: string;
  stats?: Stat[];
}

export interface Paper {
  title: string;
  meta?: string;
  url?: string;
  pdf?: string;
  links?: Link[];
  press?: Link[];
  abstract?: string;
  summary?: string;
  feature?: Feature;
}

export interface Section {
  file: string;
  title: string;
  onHomepage: boolean;
  papers: Paper[];
}

const manifest = parse(manifestRaw)['sections'] as {
  file: string;
  title: string;
  on_homepage?: boolean;
}[];

export const SECTIONS: Section[] = manifest.map(entry => ({
  file: entry.file,
  title: entry.title,
  onHomepage: !!entry.on_homepage,
  papers: parse(sectionFiles[`./sections/${entry.file}`]) as Paper[],
}));

export const HOMEPAGE_PAPERS = SECTIONS.filter(s => s.onHomepage).flatMap(s => s.papers);
