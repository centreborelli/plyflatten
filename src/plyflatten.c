// take a series of ply files and produce a digital elevation map

#include <assert.h>
#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#include "xmalloc.c"

// rescale a double:
// min: start of interval
// resolution: spacing between values
static int rescale_double_to_int(double x, double min, double resolution)
{
	int r = floor( (x - min) / resolution);
	return r;
}

static float recenter_double(int i, double xmin, double resolution)
{
	return xmin + resolution * (0.5 + i);
}

struct accumulator_image {
	float *min;
	float *max;
	float *cnt;
	float *avg;
	float *std;
	int w, h;
};

// update the output images with a new height
static void accumulate_height(
		struct accumulator_image *x,
		int i, int j,         // position of the new height
		const double *v,      // new height (and r, b, g...)
		int v_size,           // nb "extra" columns (height, r, g, b...)
		float weight)         // relative weight
{
	uint64_t k = (uint64_t) x->w * j + i;
	uint64_t k2;
	for (int l = 0; l < v_size; l++) {
		k2 = v_size*k+l;
		x->avg[k2] = (v[l] * weight + x->cnt[k] * x->avg[k2]) / (weight + x->cnt[k]);
		x->std[k2] = (pow(v[l], 2) * weight + x->cnt[k] * x->std[k2]) / (weight + x->cnt[k]);
		x->min[k2] = fmin(x->min[k2], v[l]);
		x->max[k2] = fmax(x->max[k2], v[l]);
	}
	x->cnt[k] += weight;
}

// check whether a point is inside the image domain
static int insideP(int w, int h, int i, int j)
{
	return i>=0 && j>=0 && i<w && j<h;
}

static float distance_weight(float sigma, float d)
{
	if (isinf(sigma))
		return 1;
	else
		return exp(-d*d/(2*sigma*sigma));
}


/* This function is meant to be mapped to python using ctypes. */
/* It "rasterizes" points cloud as input_buffer which is interpreted as a list of points (x, y, [z, r, g, b, ...]) */
/* The "columns" between square brackets [z (height), r, g, b, ...] are named as extra columns. */
/* The output multiband image (x->avg) is given as an argument as a linear buffer of float of size (xsize*ysize*nb_extra_columns).  */
/* This buffer is filled by the function. */

void rasterize_cloud(
		const double * input_buffer,
		float * raster_avg,
		float * raster_std,
		float * raster_min,
		float * raster_max,
		float * raster_cnt,
		const int nb_points,
		const int nb_extra_columns, // z, r, g, b, ...
		const double xoff, const double yoff,
		const double resolution,
		const int xsize, const int ysize,
		const int radius, const float sigma)
{

	// get current accumulator status
	struct accumulator_image x[1];
	x->w = xsize;
	x->h = ysize;
	x->min = raster_min;
	x->max = raster_max;
	x->cnt = raster_cnt;
	x->avg = raster_avg;
	x->std = raster_std;

	double sigma2mult2 = 2*sigma*sigma;

	// accumulate points of cloud to the image
	for (uint64_t k = 0; k < (uint64_t) nb_points; k++) {
		int ind = k * (2 + nb_extra_columns);
		double xx = input_buffer[ind];
		double yy = input_buffer[ind+1];
		int i = rescale_double_to_int(xx, xoff, resolution);
		int j = rescale_double_to_int(-yy, -yoff, resolution);

		for (int k1 = -radius; k1 <= radius; k1++)
		for (int k2 = -radius; k2 <= radius; k2++) {
			int ii = i + k1;
			int jj = j + k2;
			float dist_x = xx - recenter_double(ii, xoff, resolution);
			float dist_y = yy - recenter_double(jj, yoff, -resolution);
			float dist = hypot(dist_x, dist_y);
			float weight = distance_weight(sigma, dist);
			
			if (insideP(x->w, x->h, ii, jj)) {
				accumulate_height(x, ii, jj,
						  &(input_buffer[ind+2]),
						  nb_extra_columns, weight);
				assert(isfinite(input_buffer[ind+2]));
			}
		}
	}

}


void finishing_touches(
		float * raster_avg,
		float * raster_std,
		float * raster_min,
		float * raster_max,
		float * raster_cnt,
		const int nb_extra_columns,
		const int xsize, const int ysize)
{

	// get current accumulator status
	struct accumulator_image x[1];
	x->w = xsize;
	x->h = ysize;
	x->min = raster_min;
	x->max = raster_max;
	x->cnt = raster_cnt;
	x->avg = raster_avg;
	x->std = raster_std;

	// set unknown values to NAN
	for (uint64_t i = 0; i < (uint64_t) xsize*ysize; i++) {
		if (!x->cnt[i]){
			for (uint64_t j = 0; j < (uint64_t) nb_extra_columns; j++){
				x->avg[nb_extra_columns*i+j] = NAN;
				x->min[nb_extra_columns*i+j] = NAN;
				x->max[nb_extra_columns*i+j] = NAN;
		}
		}
		if (x->cnt[i]<2) {
			for (uint64_t j = 0; j < (uint64_t) nb_extra_columns; j++)
				x->std[nb_extra_columns*i+j] = NAN;
		}
		else {
			// so far x->std contains E[x^2] and x->avg contains E[x]
			// the standard deviation is then computed std = sqrt(E[x^2] - E[x]^2)
			for (uint64_t j = 0; j < (uint64_t) nb_extra_columns; j++)
				x->std[nb_extra_columns*i+j] = sqrt( x->std[nb_extra_columns*i+j] - pow(x->avg[nb_extra_columns*i+j], 2) );
		}
	}
}
