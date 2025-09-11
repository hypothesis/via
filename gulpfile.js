import {
  buildCSS,
  buildJS,
  generateManifest,
  runTests,
  watchJS,
} from '@hypothesis/frontend-build';
import { mkdirSync } from 'fs';
import gulp from 'gulp';

gulp.task('build-js', () => buildJS('./rollup.config.js'));
gulp.task('watch-js', () => watchJS('./rollup.config.js'));

gulp.task('build-css', () =>
  buildCSS(['./via/static/styles/video_player.css'], { autoprefixer: false, tailwind: true }),
);

gulp.task('watch-css', () => {
  gulp.watch(
    [
      './via/static/styles/**/*.{css,scss}',
      './via/static/scripts/**/*.{js,ts,tsx}',
    ],
    { ignoreInitial: false },
    gulp.series('build-css'),
  );
});

gulp.task('watch-manifest', () => {
  // Ensure build dir exists, otherwise `gulp.watch` may not work.
  mkdirSync('build', { recursive: true });
  gulp.watch('build/**/*.{css,js,map}', generateManifest);
});

gulp.task('build', gulp.series(['build-js', 'build-css'], generateManifest));
gulp.task('watch', gulp.parallel(['watch-js', 'watch-css', 'watch-manifest']));

// Unit and integration testing tasks.
//
// Some (eg. a11y) tests rely on CSS bundles. We assume that JS will always take
// longer to build than CSS, so build in parallel.
gulp.task(
  'test',
  gulp.parallel('build-css', () =>
    runTests({
      bootstrapFile: 'via/static/scripts/setup-tests.js',
      vitestConfig: 'vitest.config.js',
      rollupConfig: 'rollup-tests.config.js',
      testsPattern: 'via/static/scripts/**/*-test.js',
    }),
  ),
);
