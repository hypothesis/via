import {
  buildCSS,
  buildJS,
  generateManifest,
  runTests,
  watchJS,
} from '@hypothesis/frontend-build';
import gulp from 'gulp';

import tailwindConfig from './tailwind.config.mjs';

gulp.task('build-js', () => buildJS('./rollup.config.mjs'));
gulp.task('watch-js', () => watchJS('./rollup.config.mjs'));

gulp.task('build-css', () =>
  buildCSS(['./via/static/styles/video_player.css'], { tailwindConfig })
);

gulp.task('watch-css', () => {
  gulp.watch(
    [
      './via/static/styles/**/*.{css,scss}',
      './via/static/scripts/**/*.{js,ts,tsx}',
    ],
    { ignoreInitial: false },
    gulp.series('build-css')
  );
});

gulp.task('watch-manifest', () => {
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
      karmaConfig: 'via/static/scripts/karma.config.js',
      rollupConfig: 'rollup-tests.config.mjs',
      testsPattern: 'via/static/scripts/**/*-test.js',
    })
  )
);
